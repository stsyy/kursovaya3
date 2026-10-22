"""Взаимодействие с внешним SMS-шлюзом."""
import json
import logging
import urllib.request

from django.conf import settings

log = logging.getLogger(__name__)


class ConsoleGateway:
    """Шлюз для разработки и тестов: сообщения пишутся в журнал и сохраняются в outbox."""

    outbox = []

    def send(self, phone, text):
        self.outbox.append((phone, text))
        log.info('SMS %s: %s', phone, text)
        return True


class HttpGateway:
    """Отправка через HTTP API внешнего SMS-шлюза (JSON: phone, text, sender)."""

    def send(self, phone, text):
        body = json.dumps({'phone': phone, 'text': text, 'sender': settings.SMS_SENDER}).encode()
        req = urllib.request.Request(settings.SMS_GATEWAY_URL, data=body, method='POST', headers={
            'Content-Type': 'application/json', 'Authorization': f'Bearer {settings.SMS_GATEWAY_TOKEN}'})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return 200 <= resp.status < 300
        except OSError as e:
            log.warning('SMS-шлюз недоступен: %s', e)
            return False


def get_gateway():
    return HttpGateway() if settings.SMS_BACKEND == 'http' else ConsoleGateway()
