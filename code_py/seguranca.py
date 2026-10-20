import hashlib
import secrets

#============================= { CONFIGURAÇÃO } =============================#

iteracoes = 600_000

# Letras e dígitos sem caracteres ambíguos (0/O, 1/l/I), para facilitar o repasse da senha.
caracteres_senha = 'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'

#============================= { SEGURANÇA } =============================#

def gerar_hash_senha(senha):
# Gera um hash seguro para a senha.
    if not isinstance(senha, str) or not senha:
        raise ValueError('A senha deve ser informada.')

    sal = secrets.token_bytes(16)

    hash_senha = hashlib.pbkdf2_hmac(
        'sha256',
        senha.encode('utf-8'),
        sal,
        iteracoes
    )

    # Monta uma string com todas as informações necessárias para verificar a senha posteriormente:
    # algoritmo, número de iterações, sal e hash gerado.
    return f'pbkdf2_sha256${iteracoes}${sal.hex()}${hash_senha.hex()}'


def verificar_senha(senha_digitada, hash_armazenado):
# Verifica se a senha digitada corresponde ao hash armazenado.

    if not isinstance(senha_digitada, str):
        return False

    if not isinstance(hash_armazenado, str):
        return False

    try:
        # Separa as quatro partes do hash usando o caractere '$'.
        algoritmo, iteracoes_hash, sal_hex, hash_original = hash_armazenado.split('$')

        if algoritmo != 'pbkdf2_sha256':
            return False

        iteracoes_hash = int(iteracoes_hash)
        if not 1 <= iteracoes_hash <= 2_000_000:
            return False

        sal = bytes.fromhex(sal_hex)
        hash_original = bytes.fromhex(hash_original)

        hash_teste = hashlib.pbkdf2_hmac(
            'sha256',
            senha_digitada.encode('utf-8'),
            sal,
            iteracoes_hash
        )

        # Compare_digest() é apropriado para comparações sensíveis a tempo. Ajuda a reduzir vazamentos de informação.
        return secrets.compare_digest(hash_teste, hash_original)

    except (ValueError, TypeError):
        return False


def gerar_senha_aleatoria(tamanho=10):
# Gera uma senha inicial aleatória para ser repassada pelo admin.
    if type(tamanho) is not int or tamanho < 8:
        raise ValueError('A senha gerada deve ter pelo menos 8 caracteres.')

    return ''.join(secrets.choice(caracteres_senha) for _ in range(tamanho))
