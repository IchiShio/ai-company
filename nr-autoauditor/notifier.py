"""
NR-AutoAuditor 通知モジュール
Slack / Discord Webhook および Email (SMTP) で通知を送信する。
"""

from __future__ import annotations

import json
import logging
import smtplib
from email.mime.text import MIMEText

import httpx

from config import Config

logger = logging.getLogger(__name__)


async def notify_slack(webhook_url: str, message: str) -> bool:
    """Slack Webhook で通知"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                webhook_url,
                json={"text": message},
                timeout=10,
            )
            resp.raise_for_status()
            logger.info("Slack 通知送信完了")
            return True
    except Exception as e:
        logger.error("Slack 通知失敗: %s", e)
        return False


async def notify_discord(webhook_url: str, message: str) -> bool:
    """Discord Webhook で通知"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                webhook_url,
                json={"content": message},
                timeout=10,
            )
            resp.raise_for_status()
            logger.info("Discord 通知送信完了")
            return True
    except Exception as e:
        logger.error("Discord 通知失敗: %s", e)
        return False


def notify_email(config: Config, subject: str, body: str) -> bool:
    """SMTP でメール通知"""
    if not all([config.smtp_host, config.email_from, config.email_to]):
        logger.warning("Email 設定が不完全のためスキップ")
        return False

    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = config.email_from
        msg["To"] = config.email_to

        with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
            server.starttls()
            if config.smtp_user and config.smtp_password:
                server.login(config.smtp_user, config.smtp_password)
            server.send_message(msg)

        logger.info("Email 通知送信完了: %s", config.email_to)
        return True
    except Exception as e:
        logger.error("Email 通知失敗: %s", e)
        return False


async def send_notifications(config: Config, message: str, subject: str = "") -> None:
    """設定されている全チャネルに通知を送信"""
    if not subject:
        subject = "NR-AutoAuditor 監査結果"

    if config.slack_webhook_url:
        await notify_slack(config.slack_webhook_url, message)

    if config.discord_webhook_url:
        await notify_discord(config.discord_webhook_url, message)

    if config.smtp_host and config.email_to:
        notify_email(config, subject, message)
