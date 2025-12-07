import asyncio
import logging
from nodriver import start
from nodriver.core import Page
from nodriver.errors import NoSuchElement
from datetime import datetime

class TikTokChecker:
    def __init__(self, account_manager, captcha_solver):
        self.account_manager = account_manager
        self.captcha_solver = captcha_solver

    async def check_account(self, account):
        """Основная логика проверки аккаунта"""
        browser = await start(headless=False)
        tab: Page = await browser.get("https://www.tiktok.com/login/phone-or-email/email")

        try:
            logger.info(f"Проверяю аккаунт {account['email']}...")

            # Вводим email
            email_input = await tab.select('input[name="username"]')
            await email_input.send_keys(account['email'])
            await asyncio.sleep(1)

            # Вводим пароль
            password_input = await tab.select('input[name="password"]')
            await password_input.send_keys(account['password'])
            await asyncio.sleep(1)

            # Клик по кнопке логина
            login_button = await tab.select('button[type="submit"]')
            await login_button.click()
            logger.info("Отправил форму входа...")

            # Проверка капчи (если есть)
            try:
                captcha_frame = await tab.select('iframe[src*="captcha"]', timeout=5)
                if captcha_frame:
                    logger.warning("Обнаружена капча! Передаём в solver...")
                    await self.captcha_solver.solve(tab)
            except NoSuchElement:
                pass

            # Проверяем успешный вход (например, по наличию кнопки профиля)
            await tab.wait_for('a[href*="/profile"]', timeout=15)
            logger.info(f"✅ Аккаунт {account['email']} успешно залогинен")

            # Получаем куки
            cookies = await tab.cookies()
            account['cookies'] = cookies

            # Доп. логика — проверка статистики, публикаций и т.д.
            # await self._check_profile(tab, account)

        except Exception as e:
            logger.error(f"Ошибка при проверке {account['email']}: {e}")
        finally:
            await browser.stop()
