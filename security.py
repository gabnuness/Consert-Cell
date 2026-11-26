"""
Módulo de Segurança e Defesa contra Ataques de Força Bruta (Brute-Force & Rate Limiting).
Implementa Rate Limiter deslizante em memória com bloqueio duplo (por IP e por Conta),
mitigação de enumeração de usuários (timing attacks) e proteção contra robôs.
"""

import time
import threading
from typing import Tuple
from flask import Request
from flask_bcrypt import generate_password_hash

# Hash Bcrypt estático pré-computado para mitigação de Timing Attacks na verificação de senhas.
# Garante que requisições com usuários inexistentes demorem exatamente o mesmo tempo que senhas incorretas.
DUMMY_BCRYPT_HASH = generate_password_hash("dummy_security_timing_protection_hash_fallback_2026").decode('utf-8')


class LoginRateLimiter:
    """
    Gerenciador thread-safe de limite de tentativas e bloqueio temporário (Rate Limiting).
    Monitora tentativas por endereço IP e por e-mail/usuário alvo para mitigar:
    1. Ataques de força bruta clássicos (Single-IP, Single-Target)
    2. Ataques distribuídos de força bruta (Multi-IP, Single-Target)
    3. Credential stuffing / Dictionary attacks (Single-IP, Multi-Target)
    """

    def __init__(self, max_attempts: int = 5, window_seconds: int = 300, lockout_seconds: int = 300):
        """
        :param max_attempts: Quantidade máxima de falhas permitidas antes de bloquear.
        :param window_seconds: Janela de tempo deslizante (em segundos) para contagem de falhas (padrão: 5 min).
        :param lockout_seconds: Duração do bloqueio temporário (em segundos) ao atingir o limite (padrão: 5 min).
        """
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self._lock = threading.Lock()

        # Estruturas: chave -> lista de timestamps das tentativas falhas
        self._ip_failures = {}
        self._user_failures = {}

        # Estruturas de bloqueio: chave -> timestamp de expiração do bloqueio
        self._ip_lockouts = {}
        self._user_lockouts = {}

    def get_client_ip(self, request: Request) -> str:
        """
        Extrai o IP real do cliente considerando proxies reversos (Render, Cloudflare, Nginx, Railway).
        """
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            # O primeiro IP na lista X-Forwarded-For é o cliente original
            client_ip = forwarded.split(',')[0].strip()
            if client_ip:
                return client_ip
        return request.remote_addr or '127.0.0.1'

    def is_locked(self, ip: str, email: str = "") -> Tuple[bool, int]:
        """
        Verifica se o IP ou o e-mail alvo estão atualmente bloqueados.
        Retorna (bloqueado: bool, segundos_restantes: int).
        """
        now = time.time()
        norm_email = email.strip().lower() if email else ""

        with self._lock:
            # 1. Verifica bloqueio por IP
            if ip in self._ip_lockouts:
                if now < self._ip_lockouts[ip]:
                    return True, int(self._ip_lockouts[ip] - now) + 1
                else:
                    del self._ip_lockouts[ip]

            # 2. Verifica bloqueio por e-mail (se fornecido)
            if norm_email and norm_email in self._user_lockouts:
                if now < self._user_lockouts[norm_email]:
                    return True, int(self._user_lockouts[norm_email] - now) + 1
                else:
                    del self._user_lockouts[norm_email]

        return False, 0

    def record_failure(self, ip: str, email: str = "") -> Tuple[bool, int, int]:
        """
        Registra uma tentativa de login falha.
        Retorna (bloqueado_agora: bool, tentativas_restantes: int, segundos_bloqueio: int).
        """
        now = time.time()
        norm_email = email.strip().lower() if email else ""
        cutoff = now - self.window_seconds

        with self._lock:
            # 1. Atualiza e poda histórico do IP
            ip_attempts = [t for t in self._ip_failures.get(ip, []) if t > cutoff]
            ip_attempts.append(now)
            self._ip_failures[ip] = ip_attempts

            # 2. Atualiza e poda histórico do e-mail
            user_attempts = []
            if norm_email:
                user_attempts = [t for t in self._user_failures.get(norm_email, []) if t > cutoff]
                user_attempts.append(now)
                self._user_failures[norm_email] = user_attempts

            # Calcula maior número de tentativas recentes
            recent_count = max(len(ip_attempts), len(user_attempts))
            attempts_left = max(0, self.max_attempts - recent_count)

            # Se atingiu o limite, ativa o bloqueio temporário
            if recent_count >= self.max_attempts:
                unlock_time = now + self.lockout_seconds
                self._ip_lockouts[ip] = unlock_time
                if norm_email:
                    self._user_lockouts[norm_email] = unlock_time
                return True, 0, self.lockout_seconds

            return False, attempts_left, 0

    def record_success(self, ip: str, email: str = ""):
        """Limpa as tentativas falhas e bloqueios ao autenticar com sucesso."""
        norm_email = email.strip().lower() if email else ""
        with self._lock:
            self._ip_failures.pop(ip, None)
            self._ip_lockouts.pop(ip, None)
            if norm_email:
                self._user_failures.pop(norm_email, None)
                self._user_lockouts.pop(norm_email, None)

    def reset_all(self):
        """Zera todos os contadores e bloqueios (utilizado principalmente em testes automatizados)."""
        with self._lock:
            self._ip_failures.clear()
            self._user_failures.clear()
            self._ip_lockouts.clear()
            self._user_lockouts.clear()


# Instância global do Rate Limiter: 5 tentativas erradas em 5 minutos geram bloqueio de 5 minutos
login_limiter = LoginRateLimiter(max_attempts=5, window_seconds=300, lockout_seconds=300)
