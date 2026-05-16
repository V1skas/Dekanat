import reflex as rx

from Dekanat import routes

from Dekanat.views.auth import require_login, index as login_page
from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates.app_shell import app_shell_wrap, content_area_wrap
from Dekanat.views import application_status
from Dekanat.views import dashboard
from Dekanat.views import department
from Dekanat.views import entrant
from Dekanat.views import entrants_group
from Dekanat.views import entry_base
from Dekanat.views import identity_document_type
from Dekanat.views import item_zno
from Dekanat.views import kinship
from Dekanat.views import role
from Dekanat.views import source_of_funding
from Dekanat.views import special_condition
from Dekanat.views import speciality
from Dekanat.views import worker

from Dekanat.states.auth import AuthState
from Dekanat.states import application_status as application_status_states
from Dekanat.states import department as department_states
from Dekanat.states import entrant as entrant_states
from Dekanat.states import entrants_group as entrants_group_states
from Dekanat.states import entry_base as entry_base_states
from Dekanat.states import identity_document_type as identity_document_type_states
from Dekanat.states import item_zno as item_zno_states
from Dekanat.states import kinship as kinship_states
from Dekanat.states import role as role_states
from Dekanat.states import source_of_funding as source_of_funding_states
from Dekanat.states import special_condition as special_condition_states
from Dekanat.states import speciality as speciality_states
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

app.add_page(special_condition.list_page, route=routes.SPECIAL_CONDITION_LIST, on_load=special_condition_states.ListSpecialConditionState.on_load)
app.add_page(special_condition.add_page, route=routes.SPECIAL_CONDITION_ADD, on_load=special_condition_states.AddSpecialConditionState.on_load)
app.add_page(special_condition.edit_page, route=routes.SPECIAL_CONDITION_EDIT+"[code]", on_load=special_condition_states.EditSpecialConditionState.on_load)
app.add_page(special_condition.view_page, route=routes.SPECIAL_CONDITION_VIEW+"[code]", on_load=special_condition_states.ViewSpecialConditionState.on_load)

app.add_page(source_of_funding.list_page, route=routes.SOURCE_OF_FUNDING_LIST, on_load=source_of_funding_states.ListSourceOfFundingState.on_load)
app.add_page(source_of_funding.add_page, route=routes.SOURCE_OF_FUNDING_ADD, on_load=source_of_funding_states.AddSourceOfFundingState.on_load)
app.add_page(source_of_funding.edit_page, route=routes.SOURCE_OF_FUNDING_EDIT+"[id]", on_load=source_of_funding_states.EditSourceOfFundingState.on_load)
app.add_page(source_of_funding.view_page, route=routes.SOURCE_OF_FUNDING_VIEW+"[id]", on_load=source_of_funding_states.ViewSourceOfFundingState.on_load)

app.add_page(department.list_page, route=routes.DEPARTMENT_LIST, on_load=department_states.ListDepartmentState.on_load)
app.add_page(department.add_page, route=routes.DEPARTMENT_ADD, on_load=department_states.AddDepartmentState.on_load)
app.add_page(department.edit_page, route=routes.DEPARTMENT_EDIT+"[id]", on_load=department_states.EditDepartmentState.on_load)
app.add_page(department.view_page, route=routes.DEPARTMENT_VIEW+"[id]", on_load=department_states.ViewDepartmentState.on_load)

app.add_page(speciality.list_page, route=routes.SPECIALITY_LIST, on_load=speciality_states.ListSpecialityState.on_load)
app.add_page(speciality.add_page, route=routes.SPECIALITY_ADD, on_load=speciality_states.AddSpecialityState.on_load)
app.add_page(speciality.edit_page, route=routes.SPECIALITY_EDIT+"[dept_id]/[spec_code]", on_load=speciality_states.EditSpecialityState.on_load)
app.add_page(speciality.view_page, route=routes.SPECIALITY_VIEW+"[dept_id]/[spec_code]", on_load=speciality_states.ViewSpecialityState.on_load)

app.add_page(application_status.list_page, route=routes.APPLICATION_STATUS_LIST, on_load=application_status_states.ListApplicationStatusState.on_load)
app.add_page(application_status.add_page, route=routes.APPLICATION_STATUS_ADD, on_load=application_status_states.AddApplicationStatusState.on_load)
app.add_page(application_status.edit_page, route=routes.APPLICATION_STATUS_EDIT+"[id]", on_load=application_status_states.EditApplicationStatusState.on_load)
app.add_page(application_status.view_page, route=routes.APPLICATION_STATUS_VIEW+"[id]", on_load=application_status_states.ViewApplicationStatusState.on_load)

app.add_page(role.list_page, route=routes.ROLES_LIST, on_load=role_states.ListRoleState.on_load)
app.add_page(role.add_page, route=routes.ROLES_ADD, on_load=role_states.AddRoleState.on_load)
app.add_page(role.edit_page, route=routes.ROLES_EDIT+"[id]", on_load=role_states.EditRoleState.on_load)
app.add_page(role.view_page, route=routes.ROLES_VIEW+"[id]", on_load=role_states.ViewRoleState.on_load)

app.add_page(worker.list_page, route=routes.WORKERS_LIST, on_load=worker_states.ListWorkerState.on_load)
app.add_page(worker.add_page, route=routes.WORKERS_ADD, on_load=worker_states.AddWorkerState.on_load)
app.add_page(worker.edit_page, route=routes.WORKERS_EDIT+"[id]", on_load=worker_states.EditWorkerState.on_load)
app.add_page(worker.view_page, route=routes.WORKERS_VIEW+"[id]", on_load=worker_states.ViewWorkerState.on_load)

app.add_page(item_zno.list_page, route=routes.ITEM_ZNO_LIST, on_load=item_zno_states.ListItemZnoState.on_load)
app.add_page(item_zno.add_page, route=routes.ITEM_ZNO_ADD, on_load=item_zno_states.AddItemZnoState.on_load)
app.add_page(item_zno.edit_page, route=routes.ITEM_ZNO_EDIT+"[id]", on_load=item_zno_states.EditItemZnoState.on_load)
app.add_page(item_zno.view_page, route=routes.ITEM_ZNO_VIEW+"[id]", on_load=item_zno_states.ViewItemZnoState.on_load)

app.add_page(entry_base.list_page, route=routes.ENTRY_BASE_LIST, on_load=entry_base_states.ListEntryBaseState.on_load)
app.add_page(entry_base.add_page, route=routes.ENTRY_BASE_ADD, on_load=entry_base_states.AddEntryBaseState.on_load)
app.add_page(entry_base.edit_page, route=routes.ENTRY_BASE_EDIT+"[id]", on_load=entry_base_states.EditEntryBaseState.on_load)
app.add_page(entry_base.view_page, route=routes.ENTRY_BASE_VIEW+"[id]", on_load=entry_base_states.ViewEntryBaseState.on_load)

app.add_page(entrants_group.list_page, route=routes.ENTRANTS_GROUP_LIST, on_load=entrants_group_states.ListEntrantsGroupState.on_load)
app.add_page(entrants_group.add_page, route=routes.ENTRANTS_GROUP_ADD, on_load=entrants_group_states.AddEntrantsGroupState.on_load)
app.add_page(entrants_group.edit_page, route=routes.ENTRANTS_GROUP_EDIT+"[id]", on_load=entrants_group_states.EditEntrantsGroupState.on_load)
app.add_page(entrants_group.view_page, route=routes.ENTRANTS_GROUP_VIEW+"[id]", on_load=entrants_group_states.ViewEntrantsGroupState.on_load)

app.add_page(entrant.list_page, route=routes.ENTRANT_LIST, on_load=entrant_states.ListEntrantState.on_load)
app.add_page(entrant.add_page, route=routes.ENTRANT_ADD, on_load=entrant_states.EntrantFormState.on_load_add)
app.add_page(entrant.edit_page, route=routes.ENTRANT_EDIT+"[id]", on_load=entrant_states.EntrantFormState.on_load_edit)
app.add_page(entrant.view_page, route=routes.ENTRANT_VIEW+"[id]", on_load=entrant_states.ViewEntrantState.on_load)
