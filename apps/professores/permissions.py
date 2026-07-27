# A regra de permissão "quem pode gerenciar dados acadêmicos" é
# compartilhada por vários módulos (Professores, Disciplinas, Turmas,
# Ambientes...), então vive centralizada em apps.usuarios.permissions.
from apps.usuarios.permissions import GerenciaAcademicoMixin  # noqa: F401
