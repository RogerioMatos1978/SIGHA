#!/usr/bin/env python3
"""
Módulo 18 (Testes) — roda a suíte inteira do SIGHA de uma vez só: os 16
apps de Django (cada um com sua própria bateria de testes) mais o teste
de integração de ponta a ponta (`tests_e2e`), com relatório de cobertura
de código no final.

Uso (com o banco do projeto já rodando — Docker ou local):

    python executar_testes.py

Funciona igual em Windows, Linux ou macOS: só chama `coverage`/`manage.py
test` por baixo, sem nada específico de shell (por isso é um script
Python, e não um .sh/.bat separado por sistema operacional).

Precisa do pacote `coverage` instalado (já está no requirements.txt).
"""
import subprocess
import sys

APPS = [
    'apps.usuarios',
    'apps.dashboard',
    'apps.professores',
    'apps.disciplinas',
    'apps.turmas',
    'apps.ambientes',
    'apps.horarios',
    'apps.disponibilidade',
    'apps.grade',
    'apps.algoritmo',
    'apps.calendario',
    'apps.relatorios',
    'apps.exportacoes',
    'apps.api',
    'apps.auditoria',
    'apps.backup',
]

TESTE_DE_INTEGRACAO = 'tests_e2e.test_fluxo_completo'


def executar(comando):
    print(f'\n$ {" ".join(comando)}')
    resultado = subprocess.run(comando)
    return resultado.returncode


def main():
    codigo = executar(
        [sys.executable, '-m', 'coverage', 'run', 'manage.py', 'test']
        + APPS + [TESTE_DE_INTEGRACAO]
    )
    if codigo != 0:
        print('\nA suíte de testes falhou — veja os erros acima.')
        sys.exit(codigo)

    print('\nTodos os testes passaram. Relatório de cobertura:\n')
    executar([sys.executable, '-m', 'coverage', 'report', '-m'])
    executar([sys.executable, '-m', 'coverage', 'html'])
    print('\nRelatório HTML detalhado em htmlcov/index.html')


if __name__ == '__main__':
    main()
