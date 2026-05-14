import reflex as rx

from Dekanat import routes

from Dekanat.views.auth import require_login, index as login_page
from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates.app_shell import app_shell_wrap, content_area_wrap
from Dekanat.views import dashboard
from Dekanat.views import identity_document_type
from Dekanat.views import kinship
from Dekanat.views import role
from Dekanat.views import worker

from Dekanat.states.auth import AuthState
from Dekanat.states import identity_document_type as identity_document_type_states
from Dekanat.states import kinship as kinship_states
from Dekanat.states import role as role_states
from Dekanat.states import worker as worker_states

app = rx.App(
    theme=rx.theme(
            appearance="light",
            has_background=True,
            radius="large",
            accent_color="brown",
        )
)

# Persistent layout: шапка и сайдбар живут в app_wraps над <Outlet/> и не пересоздаются при навигации.
app.extra_app_wraps[15, "AppShell"] = app_shell_wrap
app.extra_app_wraps[10, "ContentArea"] = content_area_wrap

app.add_page(login_page, route=routes.LOGIN, on_load=AuthState.on_load)
app.add_page(dashboard.dashboard_page, route=routes.DASHBOARD)

app.add_page(identity_document_type.list_page, route=routes.IDENTITY_DOCUMENT_TYPE_LIST, on_load=identity_document_type_states.ListIdentityDocumentTypeState.on_load)
app.add_page(identity_document_type.add_page, route=routes.IDENTITY_DOCUMENT_TYPE_ADD, on_load=identity_document_type_states.AddIdentityDocumentTypeState.on_load)
app.add_page(identity_document_type.edit_page, route=routes.IDENTITY_DOCUMENT_TYPE_EDIT+"[id]", on_load=identity_document_type_states.EditIdentityDocumentTypeState.on_load)
app.add_page(identity_document_type.view_page, route=routes.IDENTITY_DOCUMENT_TYPE_VIEW+"[id]", on_load=identity_document_type_states.ViewIdentityDocumentTypeState.on_load)

app.add_page(kinship.list_page, route=routes.KINSHIP_LIST, on_load=kinship_states.ListKinshipState.on_load)
app.add_page(kinship.add_page, route=routes.KINSHIP_ADD, on_load=kinship_states.AddKinshipState.on_load)
app.add_page(kinship.edit_page, route=routes.KINSHIP_EDIT+"[id]", on_load=kinship_states.EditKinshipState.on_load)
app.add_page(kinship.view_page, route=routes.KINSHIP_VIEW+"[id]", on_load=kinship_states.ViewKinshipState.on_load)

app.add_page(role.list_page, route=routes.ROLES_LIST, on_load=role_states.ListRoleState.on_load)
app.add_page(role.add_page, route=routes.ROLES_ADD, on_load=role_states.AddRoleState.on_load)
app.add_page(role.edit_page, route=routes.ROLES_EDIT+"[id]", on_load=role_states.EditRoleState.on_load)
app.add_page(role.view_page, route=routes.ROLES_VIEW+"[id]", on_load=role_states.ViewRoleState.on_load)

app.add_page(worker.list_page, route=routes.WORKERS_LIST, on_load=worker_states.ListWorkerState.on_load)
app.add_page(worker.add_page, route=routes.WORKERS_ADD, on_load=worker_states.AddWorkerState.on_load)
app.add_page(worker.edit_page, route=routes.WORKERS_EDIT+"[id]", on_load=worker_states.EditWorkerState.on_load)
app.add_page(worker.view_page, route=routes.WORKERS_VIEW+"[id]", on_load=worker_states.ViewWorkerState.on_load)
