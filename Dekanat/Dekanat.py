import reflex as rx

from Dekanat import routes

from Dekanat.views.auth import require_login, index as login_page
from Dekanat.views.tamplates.layouts import base_layout, header_subpage
from Dekanat.views import dashboard
from Dekanat.views import identity_document_type
from Dekanat.views import kinship

from Dekanat.states import identity_document_type as identity_document_type_states
from Dekanat.states import kinship as kinship_states

app = rx.App(
    theme=rx.theme(
            appearance="light",
            has_background=True,
            radius="large",
            accent_color="brown",
        )
)

app.add_page(login_page, route=routes.LOGIN)
app.add_page(dashboard.dashboard_page, route=routes.DASHBOARD)

app.add_page(identity_document_type.list_page, route=routes.IDENTITY_DOCUMENT_TYPE_LIST, on_load=identity_document_type_states.ListIdentityDocumentTypeState.on_load)
app.add_page(identity_document_type.add_page, route=routes.IDENTITY_DOCUMENT_TYPE_ADD, on_load=identity_document_type_states.AddIdentityDocumentTypeState.on_load)
app.add_page(identity_document_type.edit_page, route=routes.IDENTITY_DOCUMENT_TYPE_EDIT+"[id]", on_load=identity_document_type_states.EditIdentityDocumentTypeState.on_load)
app.add_page(identity_document_type.view_page, route=routes.IDENTITY_DOCUMENT_TYPE_VIEW+"[id]", on_load=identity_document_type_states.ViewIdentityDocumentTypeState.on_load)

app.add_page(kinship.list_page, route=routes.KINSHIP_LIST, on_load=kinship_states.ListKinshipState.on_load)
app.add_page(kinship.add_page, route=routes.KINSHIP_ADD, on_load=kinship_states.AddKinshipState.on_load)
app.add_page(kinship.edit_page, route=routes.KINSHIP_EDIT+"[id]", on_load=kinship_states.EditKinshipState.on_load)
app.add_page(kinship.view_page, route=routes.KINSHIP_VIEW+"[id]", on_load=kinship_states.ViewKinshipSate.on_load)
