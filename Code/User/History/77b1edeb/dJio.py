# tiktok_checker_nodriver.py
import asyncio
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from loguru import logger

import nodriver  # nodriver v0.48.0
# captcha solver (may provide Nodriver support). We wrap usage to be tolerant.
try:
    from tiktok_captcha_solver import AsyncPlaywrightSolver, AsyncSolver  # try import (backwards compat)
except Exception:
    AsyncPlaywrightSolver = None
    AsyncSolver = None


@dataclass
class Config:
    sadcaptcha_api_key: str = "9d745137f012561baa0fbfd4c7885bd2"
    accounts_filename: str = "acc.txt"
    output_dir: str = "accounts"
    log_filename: str = "tiktok_checker.log"

    max_browsers: int = 1
    browser_headless: bool = False
    max_check_attempts: int = 1

    page_timeout: int = 3
    action_delay: float = 0.5
    comment_delay: float = 1.0

    enable_commenting: bool = True
    enable_reply_commenting: bool = True
    enable_liking: bool = True
    enable_next_video: bool = True

    enable_comment_loop: bool = True
    comment_loop_count: int = 0
    comment_loop_delay: int = 1

    comment_text: str = "Мальчики, оцените историю😅🍑"
    comment_texts: List[str] = field(default_factory=list)

    enable_hanging: bool = True
    hang_check_interval: int = 60

    browser_args: List[str] = field(default_factory=lambda: [
        '--no-sandbox',
        '--disable-gpu',
        '--disable-dev-shm-usage',
        '--disable-extensions',
        '--disable-setuid-sandbox',
        '--disable-infobars',
        '--disable-web-security',
        '--disable-features=IsolateOrigins,site-per-process',
        '--disable-site-isolation-trials',
        '--ignore-certificate-errors',
        '--disable-accelerated-2d-canvas',
        '--disable-browser-side-navigation',
        '--disable-default-apps',
        '--no-first-run'
    ])

    browser_context_options: Dict[str, Any] = field(default_factory=lambda: {
        'viewport': {'width': 1260, 'height': 700},
        'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        'ignore_https_errors': True,
        'java_script_enabled': True,
    })


class Stats:
    def __init__(self):
        self.counters = {
            'total_accounts': 0,
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'errors': 0,
            'comments': 0,
            'replies': 0,
            'likes': 0,
            'next_videos': 0,
            'comment_loops': 0,
            'comments_per_video': {},
        }
        self.start_time = datetime.now()
        self.lock = asyncio.Lock()

    async def increment(self, key: str, value: int = 1):
        async with self.lock:
            self.counters[key] = self.counters.get(key, 0) + value

    async def get_report(self) -> str:
        async with self.lock:
            runtime = datetime.now() - self.start_time
            report = f"Статистика:\n"
            report += f"Время работы: {runtime}\n"
            report += f"Обработано: {self.counters['processed']}/{self.counters['total_accounts']} | "
            report += f"Успешно: {self.counters['successful']} | "
            report += f"Неуспешно: {self.counters['failed']} | "
            report += f"Ошибки: {self.counters['errors']}\n"

            if any(self.counters.get(k, 0) > 0 for k in ['comments', 'replies', 'likes', 'next_videos']):
                report += f"Действия: "
                report += f"Комментарии: {self.counters.get('comments', 0)} | "
                report += f"Ответы: {self.counters.get('replies', 0)} | "
                report += f"Лайки: {self.counters.get('likes', 0)} | "
                report += f"Переходы: {self.counters.get('next_videos', 0)}"

            if self.counters.get('comment_loops', 0) > 0:
                report += f"\nЦиклы комментирования: {self.counters.get('comment_loops', 0)}"

            if self.counters.get('comments_per_video', {}):
                report += "\nСтатистика по видео:"
                for video_id, count in self.counters.get('comments_per_video', {}).items():
                    report += f"\n - {video_id}: {count} комментариев"

            return report


class FileHandler:
    def __init__(self, config: Config):
        self.config = config
        os.makedirs(config.output_dir, exist_ok=True)

    def save_account(self, email: str, password: str, cookies: List[Dict]) -> bool:
        safe_filename = f"{self.config.output_dir}/{email.replace(':', '_')}.txt"
        try:
            with open(safe_filename, 'w', encoding='utf-8') as f:
                f.write(f"{email}:{password}\n")
                f.write("Успешный вход - скрипт находится в режиме ожидания")
            logger.info(f"Аккаунт {email} - ВАЛИДНЫЙ ✓ | Сохранен в {safe_filename}")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения аккаунта {email}: {type(e).__name__}: {str(e)}")
            return False

    def read_accounts(self) -> List[Dict]:
        accounts = []
        try:
            with open(self.config.accounts_filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if ':' in line:
                        email, password = line.split(':', 1)
                        accounts.append({'email': email, 'password': password})
            logger.info(f"Загружено {len(accounts)} аккаунтов из {self.config.accounts_filename}")
        except Exception as e:
            logger.error(f"Ошибка чтения аккаунтов из {self.config.accounts_filename}: {type(e).__name__}: {str(e)}")
        return accounts


# --- Небольшие helper-обёртки для nodriver, чтобы поведение было ближе к Playwright ---
async def _select_all(page, selector: str) -> List[Any]:
    """
    Возвращает список элементов под селектором.
    В nodriver чаще используется page.select(selector) -> list
    """
    try:
        els = await page.select(selector)
        return els or []
    except Exception:
        # Иногда API может называться query or find — пробуем альтернативы
        try:
            els = await page.find_all(selector)  # возможный альтернативный метод
            return els or []
        except Exception:
            return []


async def _select_one(page, selector: str) -> Optional[Any]:
    els = await _select_all(page, selector)
    return els[0] if els else None


class CaptchaSolverAdapter:
    """
    Адаптер для tiktok_captcha_solver — делает best-effort: если пакет поддерживает Nodriver,
    попытается его использовать; иначе gracefully no-op.
    """
    def __init__(self, page, api_key: str):
        self.page = page
        self.api_key = api_key
        self._solver = None
        self._init_solver()

    def _init_solver(self):
        # Попытка: если в пакете есть универсальный AsyncSolver — используем его.
        # Если нет, попробуем инициализировать AsyncPlaywrightSolver (возможно оно не совместимо).
        try:
            if AsyncSolver:
                # предположим, что AsyncSolver умеет работать с nodriver-страницей
                self._solver = AsyncSolver(page=self.page, sadcaptcha_api_key=self.api_key)
                logger.info("Captcha solver: инициализирован AsyncSolver")
                return
        except Exception as e:
            logger.warning(f"Captcha solver: не удалось инициализировать AsyncSolver: {e}")

        try:
            if AsyncPlaywrightSolver:
                # Попытка инициализировать — может не работать с nodriver, поэтому обёртываем
                self._solver = AsyncPlaywrightSolver(page=self.page, sadcaptcha_api_key=self.api_key)
                logger.info("Captcha solver: инициализирован AsyncPlaywrightSolver (best-effort)")
                return
        except Exception as e:
            logger.warning(f"Captcha solver: не удалось инициализировать AsyncPlaywrightSolver: {e}")

        # Если не удалось — оставляем None и будем делать no-op
        logger.warning("Captcha solver не доступен — solve_captcha_if_present будет пропускаться")

    async def solve_captcha_if_present(self):
        if not self._solver:
            return None
        try:
            # Универсальный интерфейс (solver должен предоставлять метод solve/solve_captcha_if_present)
            if hasattr(self._solver, "solve_captcha_if_present"):
                return await self._solver.solve_captcha_if_present()
            elif hasattr(self._solver, "solve"):
                return await self._solver.solve()
            else:
                logger.debug("Captcha solver: нет известного метода solve — пропускаем")
                return None
        except Exception as e:
            logger.warning(f"Ошибка в captcha solver: {type(e).__name__}: {e}")
            return None


class TikTokActions:
    def __init__(self, page, config: Config, stats: Stats):
        self.page = page
        self.config = config
        self.stats = stats
        self.current_video_id = "unknown"
        import random
        self.random = random

    def get_comment_text(self) -> str:
        if self.config.comment_texts:
            return self.random.choice(self.config.comment_texts)
        return self.config.comment_text

    async def update_video_id(self):
        try:
            # page.url в nodriver доступен как атрибут .url
            current_url = getattr(self.page, "url", None)
            if not current_url:
                # иногда page.current_url или page.get_url()
                try:
                    current_url = await self.page.url  # best-effort
                except Exception:
                    try:
                        current_url = await self.page.get_url()
                    except Exception:
                        current_url = ""
            if "video/" in (current_url or ""):
                self.current_video_id = (current_url.split("video/")[1].split("?")[0])
            else:
                self.current_video_id = f"video_{datetime.now().strftime('%H%M%S')}"
            if self.current_video_id not in self.stats.counters['comments_per_video']:
                self.stats.counters['comments_per_video'][self.current_video_id] = 0
        except Exception as e:
            logger.warning(f"Не удалось определить ID видео: {e}")
            self.current_video_id = f"unknown_{datetime.now().strftime('%H%M%S')}"

    async def reply_to_comment(self, email: str) -> bool:
        if not self.config.enable_reply_commenting:
            return False
        try:
            reply_button = await _select_one(self.page, 'span[data-e2e="comment-reply-1"]')
            if not reply_button:
                logger.debug("reply_to_comment: reply button not found")
                return False
            await reply_button.click()
            await asyncio.sleep(self.config.comment_delay)

            reply_input = None
            # попробуем получить последнее поле ввода
            inputs = await _select_all(self.page, 'div[data-e2e="comment-input"]')
            if inputs:
                reply_input = inputs[-1]
            if not reply_input:
                logger.debug("reply_to_comment: reply input not found")
                return False

            await reply_input.click()
            await asyncio.sleep(self.config.action_delay)

            comment_text = self.get_comment_text()
            # typing -> send_keys
            await reply_input.send_keys(comment_text)
            await asyncio.sleep(self.config.action_delay)

            # отправка Enter
            try:
                await reply_input.send_keys("\n")
            except Exception:
                # альтернатива: выполнить javascript submit
                try:
                    await self.page.exec_script("document.activeElement.dispatchEvent(new KeyboardEvent('keydown',{'key':'Enter'}));")
                except Exception:
                    pass

            await asyncio.sleep(self.config.comment_delay)
            logger.success(f"Успешно оставлен ответ на комментарий для {email}")
            await self.stats.increment('replies')
            return True
        except Exception as e:
            logger.warning(f"Не удалось ответить на комментарий: {type(e).__name__}: {str(e)}")
            return False

    async def post_comment(self, email: str) -> bool:
        if not self.config.enable_commenting:
            return False
        try:
            await self.update_video_id()

            comment_input = await _select_one(self.page, 'div[data-e2e="comment-input"]')
            if not comment_input:
                logger.warning("post_comment: поле ввода комментария не найдено")
                return False
            await comment_input.click()
            await asyncio.sleep(self.config.action_delay)

            comment_text = self.get_comment_text()
            await comment_input.send_keys(comment_text)
            await asyncio.sleep(self.config.action_delay)

            try:
                await comment_input.send_keys("\n")
            except Exception:
                # fallback
                pass

            await asyncio.sleep(self.config.comment_delay)
            await self.stats.increment('comments')
            self.stats.counters['comments_per_video'][self.current_video_id] = \
                self.stats.counters['comments_per_video'].get(self.current_video_id, 0) + 1

            logger.success(
                f"Успешно оставлен комментарий для {email} (Видео: {self.current_video_id}, #{self.stats.counters['comments_per_video'][self.current_video_id]})")
            return True
        except Exception as e:
            logger.error(f"Ошибка при оставлении комментария: {type(e).__name__}: {str(e)}")
            return False

    async def like_video(self, email: str) -> bool:
        if not self.config.enable_liking:
            return False
        try:
            like_button_browse = await _select_one(self.page, 'strong[data-e2e="browse-like-count"]')
            like_button_standard = await _select_one(self.page, 'strong[data-e2e="like-count"]')

            if like_button_browse:
                await like_button_browse.click()
                await asyncio.sleep(self.config.action_delay)
                logger.success(f"Успешно поставлен лайк (browse-like-count) для {email}")
                await self.stats.increment('likes')
                return True
            elif like_button_standard:
                await like_button_standard.click()
                await asyncio.sleep(self.config.action_delay)
                logger.success(f"Успешно поставлен лайк (like-count) для {email}")
                await self.stats.increment('likes')
                return True
            else:
                logger.warning("Не найдена кнопка лайка")
                return False
        except Exception as e:
            logger.error(f"Ошибка при постановке лайка: {type(e).__name__}: {str(e)}")
            return False

    async def next_video(self, email: str, captcha_solver: CaptchaSolverAdapter) -> bool:
        if not self.config.enable_next_video:
            return False
        try:
            logger.info(f"Пытаемся найти и нажать на кнопку Следующее видео для {email}")
            next_video_button = await _select_one(self.page, 'button[data-e2e="arrow-right"]')
            if next_video_button:
                await next_video_button.click()
                await asyncio.sleep(self.config.action_delay)
                logger.success(f"Успешно нажали на кнопку Следующее видео для {email}")
                await self.stats.increment('next_videos')
                await captcha_solver.solve_captcha_if_present()
                await self.update_video_id()
                return True
            else:
                alt = await _select_one(self.page, '.css-1s9jpf8-ButtonBasicButtonContainer-StyledVideoSwitch')
                if alt:
                    await alt.click()
                    await asyncio.sleep(self.config.action_delay)
                    logger.success(f"Успешно нажали на кнопку Следующее видео (по CSS классу) для {email}")
                    await self.stats.increment('next_videos')
                    await self.update_video_id()
                    await captcha_solver.solve_captcha_if_present()
                    return True
                else:
                    logger.warning("Не удалось найти кнопку Следующее видео")
                    return False
        except Exception as e:
            logger.error(f"Ошибка при нажатии на кнопку Следующее видео: {type(e).__name__}: {str(e)}")
            return False

    async def run_comment_loop(self, email: str, captcha_solver: CaptchaSolverAdapter):
        if not self.config.enable_comment_loop:
            return

        loop_count = 0
        max_loops = self.config.comment_loop_count
        comments_opened = False

        try:
            try:
                comments_section = await _select_all(self.page, 'div[data-e2e="comment-input"]')
                if len(comments_section) == 0:
                    comments_button = await _select_one(self.page, 'span[data-e2e="comment-icon"]')
                    if comments_button:
                        await comments_button.click()
                        await captcha_solver.solve_captcha_if_present()
                        await asyncio.sleep(self.config.comment_delay)
                        comments_opened = True
                        logger.info(f"Комментарии успешно открыты для {email}")
                    else:
                        logger.warning("Кнопка открытия комментариев не найдена")
                        return
                else:
                    comments_opened = True
                    logger.info(f"Комментарии уже открыты для {email}")
            except Exception as e:
                logger.warning(f"Не удалось открыть секцию комментариев: {e}")
                return

            while max_loops == 0 or loop_count < max_loops:
                if self.config.enable_reply_commenting:
                    try:
                        reply_success = await self.reply_to_comment(email)
                        if reply_success:
                            logger.success(f"Успешно ответили на комментарий в цикле {loop_count + 1}")
                    except Exception as e:
                        logger.warning(f"Ошибка при ответе на комментарий: {type(e).__name__}: {str(e)}")

                comment_success = await self.post_comment(email)

                if comment_success:
                    loop_count += 1
                    await self.stats.increment('comment_loops')
                    logger.info(
                        f"Цикл комментирования {loop_count}{' из ' + str(max_loops) if max_loops > 0 else ''} завершен")

                    if self.config.enable_liking:
                        await self.like_video(email)

                    if self.config.enable_next_video:
                        next_success = await self.next_video(email, captcha_solver)
                        if not next_success:
                            logger.warning("Не удалось перейти к следующему видео, продолжаем с текущим")

                    if max_loops == 0 or loop_count < max_loops:
                        logger.info(f"Ожидание {self.config.comment_loop_delay} секунд перед следующим циклом")
                        await asyncio.sleep(self.config.comment_loop_delay)
                else:
                    logger.warning(f"Не удалось оставить комментарий в цикле {loop_count + 1}")
                    if await self.next_video(email, captcha_solver):
                        logger.info("Перешли к следующему видео после неудачной попытки комментирования")
                    else:
                        logger.error("Не удалось найти новое видео для комментирования")
                        break

        except Exception as e:
            logger.error(f"Ошибка в цикле комментирования: {type(e).__name__}: {str(e)}")

        logger.info(f"Цикл комментирования завершен. Всего комментариев: {self.stats.counters['comments']}")


class TikTokChecker:
    def __init__(self, config: Config, stats: Stats):
        self.config = config
        self.stats = stats
        self.file_handler = FileHandler(config)
        self.successful_logins = []

    async def _start_browser(self):
        """
        Запуск nodriver. API nodriver.start может принимать разные аргументы.
        Подбираем самые распространённые: headless, args, user_agent.
        Если ваша версия nodriver использует другие аргументы — подкорректируйте здесь.
        """
        try:
            browser = await nodriver.start(
                headless=self.config.browser_headless,
                args=self.config.browser_args,
                user_agent=self.config.browser_context_options.get('user_agent')
            )
            return browser
        except TypeError:
            # fallback если nodriver.start не принимает user_agent/args как kwargs
            browser = await nodriver.start(headless=self.config.browser_headless)
            return browser
        except Exception:
            raise

    async def check_account(self, account: Dict) -> bool:
        email = account['email']
        password = account['password']

        for attempt in range(1, self.config.max_check_attempts + 1):
            if attempt > 1:
                logger.info(f"Повторная попытка {attempt}/{self.config.max_check_attempts} для {email}")

            browser = None
            page = None

            try:
                # Запуск браузера
                browser = await self._start_browser()

                # Открываем новую вкладку/страницу
                # API nodriver: browser.open(url) -> page
                page = await browser.get("about:blank")
                # применим размеры viewport (если nodriver поддерживает set_viewport)
                try:
                    viewport = self.config.browser_context_options.get('viewport')
                    if viewport:
                        await page.set_viewport(viewport['width'], viewport['height'])
                except Exception:
                    pass

                # Инициализируем решатель капчи (адаптер)
                captcha_solver = CaptchaSolverAdapter(page=page, api_key=self.config.sadcaptcha_api_key)

                # Переход на страницу логина
                try:
                    await page.open('https://www.tiktok.com/login/phone-or-email/email')
                except Exception:
                    # если нет page.open, используем page.goto / page.navigate / browser.open
                    try:
                        await page.goto('https://www.tiktok.com/login/phone-or-email/email')
                    except Exception:
                        try:
                            await browser.open('https://www.tiktok.com/login/phone-or-email/email')
                        except Exception:
                            logger.warning("Не удалось выполнить переход на страницу логина стандартным способом")

                await asyncio.sleep(self.config.action_delay)

                # Локаторы элементов формы
                email_input = await _select_one(page, 'input[type="text"]')
                password_input = await _select_one(page, 'input[type="password"]')
                login_button = await _select_one(page, 'button[data-e2e="login-button"], button[type="submit"]')

                if not email_input or not password_input or not login_button:
                    logger.warning(f"Не удалось загрузить форму входа для {email}")
                    # возможно страница еще не прогрузилась — небольшая пауза и повтор
                    await asyncio.sleep(2)
                    email_input = await _select_one(page, 'input[type="text"]')
                    password_input = await _select_one(page, 'input[type="password"]')
                    login_button = await _select_one(page, 'button[data-e2e="login-button"], button[type="submit"]')
                    if not email_input or not password_input or not login_button:
                        logger.warning(f"Форма входа так и не найдена для {email}")
                        continue

                # Заполнение формы
                await email_input.click()
                await asyncio.sleep(self.config.action_delay)
                await email_input.send_keys(email)
                await asyncio.sleep(self.config.action_delay)

                await password_input.click()
                await asyncio.sleep(self.config.action_delay)
                await password_input.send_keys(password)
                await asyncio.sleep(self.config.action_delay)

                await login_button.click()
                await asyncio.sleep(self.config.action_delay)

                # Попытка решить капчу
                try:
                    await captcha_solver.solve_captcha_if_present()
                except Exception as e:
                    logger.warning(f"Ошибка решения капчи: {type(e).__name__}: {str(e)}")

                # Ждём завершения входа
                await asyncio.sleep(8)

                # Проверка на код верификации
                try:
                    verification_code = await _select_one(page, '.verification-code-input, input[name="verifyCode"]')
                    if verification_code:
                        logger.warning(f"Аккаунт {email} требует код верификации")
                        await self.stats.increment('failed')
                        # Закрываем браузер чтобы не держать ресурсы (если не режим висения)
                        try:
                            await browser.close()
                        except Exception:
                            pass
                        return False
                except Exception:
                    pass

                # Проверка URL — если остались на странице login => неуспешно
                current_url = getattr(page, "url", None)
                if not current_url:
                    try:
                        current_url = await page.url
                    except Exception:
                        current_url = ""
                if current_url and "login" in current_url:
                    logger.warning(f"Аккаунт {email} - НЕВАЛИДНЫЙ ✗")
                    await self.stats.increment('failed')
                    try:
                        await browser.close()
                    except Exception:
                        pass
                    return False

                # Сохраняем аккаунт (cookies можно собрать при необходимости)
                success = self.file_handler.save_account(email, password, [])

                if success:
                    logger.success(f"Успешный вход в аккаунт {email}")
                    await self.stats.increment('successful')

                    actions = TikTokActions(page, self.config, self.stats)

                    try:
                        if self.config.enable_liking:
                            await actions.like_video(email)

                        if self.config.enable_comment_loop:
                            logger.info(f"Запуск цикла комментирования для {email}")
                            await actions.run_comment_loop(email, captcha_solver)
                        else:
                            comments_button = await _select_one(page, 'span[data-e2e="comment-icon"]')
                            if comments_button:
                                await comments_button.click()
                                await captcha_solver.solve_captcha_if_present()
                                await asyncio.sleep(self.config.comment_delay)

                            await actions.reply_to_comment(email)
                            await actions.post_comment(email)
                            await actions.next_video(email, captcha_solver)

                    except Exception as e:
                        logger.error(f"Ошибка при выполнении действий для {email}: {type(e).__name__}: {str(e)}")

                    try:
                        report = await self.stats.get_report()
                        logger.info(f"Текущая статистика действий:\n{report}")
                    except Exception as e:
                        logger.error(f"Ошибка при формировании отчета: {e}")

                    if self.config.enable_hanging:
                        # Сохраняем browser для "висения"
                        self.successful_logins.append((browser, page))
                        return True
                    else:
                        try:
                            await browser.close()
                        except Exception:
                            pass
                        return True

            except Exception as e:
                logger.error(f"Ошибка проверки {email}: {type(e).__name__}: {str(e)}")
                if browser:
                    try:
                        await browser.close()
                    except Exception:
                        pass

                if attempt == self.config.max_check_attempts:
                    logger.warning(f"Аккаунт {email} - ОШИБКА ✗")
                    await self.stats.increment('errors')
                    return False

                await asyncio.sleep(1)

        return False


class AccountProcessor:
    def __init__(self, accounts: List[Dict], config: Config):
        self.accounts = accounts
        self.config = config
        self.stats = Stats()
        self.checker = TikTokChecker(config, self.stats)
        self.next_index = 0
        self.lock = asyncio.Lock()

    async def worker(self, worker_id: int, semaphore: asyncio.Semaphore):
        while True:
            async with self.lock:
                if self.next_index >= len(self.accounts):
                    break
                account_index = self.next_index
                self.next_index += 1
                current_account = self.accounts[account_index]
                current_account['index'] = account_index + 1

            async with semaphore:
                email = current_account['email']
                logger.info(f"[{account_index + 1}/{len(self.accounts)}] Проверка {email}")
                try:
                    await self.checker.check_account(current_account)
                    async with self.lock:
                        await self.stats.increment('processed')
                        if self.stats.counters['processed'] % 5 == 0 or self.stats.counters['processed'] == len(self.accounts):
                            report = await self.stats.get_report()
                            logger.info(report)
                except Exception as e:
                    logger.error(f"Критическая ошибка проверки {email}: {type(e).__name__}: {str(e)}")
                    async with self.lock:
                        await self.stats.increment('processed')
                        await self.stats.increment('errors')

    async def process_all(self):
        if not self.accounts:
            logger.warning("Нет аккаунтов для проверки")
            return

        await self.stats.increment('total_accounts', len(self.accounts))
        logger.info(f"Начинаем проверку {len(self.accounts)} аккаунтов")

        semaphore = asyncio.Semaphore(self.config.max_browsers)
        tasks = []
        for worker_id in range(min(self.config.max_browsers, len(self.accounts))):
            task = asyncio.create_task(self.worker(worker_id + 1, semaphore))
            tasks.append(task)

        await asyncio.gather(*tasks)

        report = await self.stats.get_report()
        logger.success("Проверка аккаунтов завершена!")
        logger.success(report)

        if self.checker.successful_logins and self.config.enable_hanging:
            logger.info(f"Успешный вход в {len(self.checker.successful_logins)} аккаунтов. Скрипт находится в режиме ожидания...")
            try:
                while True:
                    logger.info("Скрипт продолжает работу... Сессии браузера активны.")
                    await asyncio.sleep(self.config.hang_check_interval)
            except KeyboardInterrupt:
                logger.info("Получен сигнал остановки. Закрываем браузеры...")
                for browser, page in self.checker.successful_logins:
                    try:
                        await browser.close()
                    except:
                        pass


async def main():
    logger.remove()
    logger.add("tiktok_checker.log", rotation="10 MB", level="INFO")
    logger.add(lambda msg: print(msg, end=""), colorize=True, level="INFO", format="{time:HH:mm:ss} | <level>{message}</level>")

    logger.info("=" * 60)
    logger.info("Th - проверка аккаунтов (nodriver)")
    logger.info("=" * 60)

    config = Config()
    file_handler = FileHandler(config)
    accounts = file_handler.read_accounts()

    processor = AccountProcessor(accounts, config)
    await processor.process_all()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Скрипт остановлен пользователем")
