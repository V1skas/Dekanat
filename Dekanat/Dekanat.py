import reflex as rx
from reflex.event import EventType

from Dekanat import routes
from Dekanat.utils.db import register_ua_collation

# Реєструємо UA_CI collation для коректного сортування кирилиці (DK-23).
register_ua_collation()

from Dekanat.views.auth import require_login, index as login_page
from Dekanat.views.templates.layouts import page_wrapper, header_subpage
from Dekanat.views.templates.app_shell import app_shell_wrap, content_area_wrap
from Dekanat.views import account
from Dekanat.views import admission_campaign
from Dekanat.views import admission_campaign_report
from Dekanat.views import app_setting
from Dekanat.views import rating
from Dekanat.views import registration_journal
from Dekanat.views import application_status
from Dekanat.views import dashboard
from Dekanat.views import department
from Dekanat.views import entrant
from Dekanat.views import entrant_application
from Dekanat.views import entrant_exam
from Dekanat.views import entrants_group
from Dekanat.views import entry_base
from Dekanat.views import form_of_study
from Dekanat.views import identity_document_type
from Dekanat.views import item_zno
from Dekanat.views import kinship
from Dekanat.views import role
from Dekanat.views import source_of_funding
from Dekanat.views import special_condition
from Dekanat.views import speciality
from Dekanat.views import worker

from Dekanat.states.app import AppState
from Dekanat.states.auth import AuthState
from Dekanat.states.audit import AuditHistoryState
from Dekanat.actions import Actions
from Dekanat.states import account as account_states
from Dekanat.states import admission_campaign as admission_campaign_states
from Dekanat.states import admission_campaign_report as admission_campaign_report_states
from Dekanat.states import app_setting as app_setting_states
from Dekanat.states import rating as rating_states
from Dekanat.states import registration_journal as registration_journal_states
from Dekanat.states import application_status as application_status_states
from Dekanat.states import department as department_states
from Dekanat.states import entrant as entrant_states
from Dekanat.states import entrant_application as entrant_application_states
from Dekanat.states import entrant_exam as entrant_exam_states
from Dekanat.states import entrants_group as entrants_group_states
from Dekanat.states import entry_base as entry_base_states
from Dekanat.states import form_of_study as form_of_study_states
from Dekanat.states import identity_document_type as identity_document_type_states
from Dekanat.states import item_zno as item_zno_states
from Dekanat.states import kinship as kinship_states
from Dekanat.states import role as role_states
from Dekanat.states import source_of_funding as source_of_funding_states
from Dekanat.states import special_condition as special_condition_states
from Dekanat.states import speciality as speciality_states
from Dekanat.states import worker as worker_states

def protected_on_load(*handlers: EventType[()]) -> EventType[()]:
    """Домішує `AppState.require_auth` першим у `on_load` захищеної сторінки (DK-66).

    Раніше міст cookie→state тримався на `on_mount` спіннера в `require_login`
    (`views/auth.py`), що ненадійно з persistent layout: нова вкладка інколи
    встигала показати спіннер до того, як `on_mount` спрацював, і користувача
    кидало на `/login`, хоча cookie валідна. `on_load` виконується гарантовано
    після гідратації, тож `require_auth` там бачить cookie `token` одразу."""
    result: list = [AppState.require_auth]
    for h in handlers:
        if isinstance(h, list):
            result.extend(h)
        elif h is not None:
            result.append(h)
    return result


app = rx.App(
    theme=rx.theme(
            appearance="light",
            has_background=True,
            radius="large",
            accent_color="brown",
        ),
    # Мова інтерфейсу — українська. Забороняємо авто-переклад браузера (Chrome
    # Translate / Gemini): він переписує текстові вузли DOM, а React/Radix при
    # оновленні rx.select падає з `NotFoundError: removeChild ... not a child`
    # (напр. при виборі джерела фінансування в анкеті абітурієнта). translate="no"
    # + notranslate-мета вимикають переклад і прибирають цей краш.
    html_lang="uk",
    html_custom_attrs={"translate": "no"},
    head_components=[
        rx.el.meta(name="google", content="notranslate"),
    ],
)

# Persistent layout: шапка и сайдбар живут в app_wraps над <Outlet/> и не пересоздаются при навигации.
app.extra_app_wraps[15, "AppShell"] = app_shell_wrap
app.extra_app_wraps[10, "ContentArea"] = content_area_wrap

# Коренева сторінка "/" — одразу редіректить на /dashboard (DK-31). Авторизацію
# далі бере на себе сам dashboard через @require_login.
app.add_page(
    rx.center(rx.spinner(size="3"), height="100vh"),
    route="/",
    on_load=rx.redirect(routes.DASHBOARD),
)
app.add_page(login_page, route=routes.LOGIN, on_load=AuthState.on_load)
app.add_page(account.settings_page, route=routes.ACCOUNT_SETTINGS, on_load=protected_on_load(account_states.AccountSettingsState.on_load))
app.add_page(dashboard.dashboard_page, route=routes.DASHBOARD, on_load=protected_on_load())
app.add_page(dashboard.base_dashboard_page, route=routes.DASHBOARD_BASE, on_load=protected_on_load())
app.add_page(dashboard.contingent_dashboard_page, route=routes.DASHBOARD_CONTINGENT, on_load=protected_on_load())
app.add_page(dashboard.admission_commission_dashboard_page, route=routes.DASHBOARD_ADMISSION_COMMISSION, on_load=protected_on_load())
app.add_page(dashboard.admin_dashboard_page, route=routes.DASHBOARD_ADMIN, on_load=protected_on_load())
app.add_page(dashboard.reporting_dashboard_page, route=routes.DASHBOARD_REPORTING, on_load=protected_on_load())
app.add_page(admission_campaign_report.list_page, route=routes.REPORT_ADMISSION, on_load=protected_on_load(admission_campaign_report_states.ListAdmissionReportState.on_load))
app.add_page(registration_journal.list_page, route=routes.REPORT_JOURNAL, on_load=protected_on_load(registration_journal_states.ListRegistrationJournalState.on_load))

app.add_page(identity_document_type.list_page, route=routes.IDENTITY_DOCUMENT_TYPE_LIST, on_load=protected_on_load(identity_document_type_states.ListIdentityDocumentTypeState.on_load))
app.add_page(identity_document_type.add_page, route=routes.IDENTITY_DOCUMENT_TYPE_ADD, on_load=protected_on_load(identity_document_type_states.AddIdentityDocumentTypeState.on_load))
app.add_page(identity_document_type.edit_page, route=routes.IDENTITY_DOCUMENT_TYPE_EDIT+"[id]", on_load=protected_on_load(identity_document_type_states.EditIdentityDocumentTypeState.on_load))
app.add_page(identity_document_type.view_page, route=routes.IDENTITY_DOCUMENT_TYPE_VIEW+"[id]", on_load=protected_on_load([identity_document_type_states.ViewIdentityDocumentTypeState.on_load, AuditHistoryState.load("identity_document_type", Actions.IDENTITY_DOCUMENT_TYPE_HISTORY_VIEW.value, Actions.IDENTITY_DOCUMENT_TYPE_HISTORY_DETAIL.value)]))

app.add_page(kinship.list_page, route=routes.KINSHIP_LIST, on_load=protected_on_load(kinship_states.ListKinshipState.on_load))
app.add_page(kinship.add_page, route=routes.KINSHIP_ADD, on_load=protected_on_load(kinship_states.AddKinshipState.on_load))
app.add_page(kinship.edit_page, route=routes.KINSHIP_EDIT+"[id]", on_load=protected_on_load(kinship_states.EditKinshipState.on_load))
app.add_page(kinship.view_page, route=routes.KINSHIP_VIEW+"[id]", on_load=protected_on_load([kinship_states.ViewKinshipState.on_load, AuditHistoryState.load("kinship", Actions.KINSHIP_HISTORY_VIEW.value, Actions.KINSHIP_HISTORY_DETAIL.value)]))

app.add_page(special_condition.list_page, route=routes.SPECIAL_CONDITION_LIST, on_load=protected_on_load(special_condition_states.ListSpecialConditionState.on_load))
app.add_page(special_condition.add_page, route=routes.SPECIAL_CONDITION_ADD, on_load=protected_on_load(special_condition_states.AddSpecialConditionState.on_load))
app.add_page(special_condition.edit_page, route=routes.SPECIAL_CONDITION_EDIT+"[code]", on_load=protected_on_load(special_condition_states.EditSpecialConditionState.on_load))
app.add_page(special_condition.view_page, route=routes.SPECIAL_CONDITION_VIEW+"[code]", on_load=protected_on_load([special_condition_states.ViewSpecialConditionState.on_load, AuditHistoryState.load("special_conditions", Actions.SPECIAL_CONDITION_HISTORY_VIEW.value, Actions.SPECIAL_CONDITION_HISTORY_DETAIL.value, "code")]))

app.add_page(source_of_funding.list_page, route=routes.SOURCE_OF_FUNDING_LIST, on_load=protected_on_load(source_of_funding_states.ListSourceOfFundingState.on_load))
app.add_page(source_of_funding.add_page, route=routes.SOURCE_OF_FUNDING_ADD, on_load=protected_on_load(source_of_funding_states.AddSourceOfFundingState.on_load))
app.add_page(source_of_funding.edit_page, route=routes.SOURCE_OF_FUNDING_EDIT+"[id]", on_load=protected_on_load(source_of_funding_states.EditSourceOfFundingState.on_load))
app.add_page(source_of_funding.view_page, route=routes.SOURCE_OF_FUNDING_VIEW+"[id]", on_load=protected_on_load([source_of_funding_states.ViewSourceOfFundingState.on_load, AuditHistoryState.load("source_of_funding", Actions.SOURCE_OF_FUNDING_HISTORY_VIEW.value, Actions.SOURCE_OF_FUNDING_HISTORY_DETAIL.value)]))

app.add_page(department.list_page, route=routes.DEPARTMENT_LIST, on_load=protected_on_load(department_states.ListDepartmentState.on_load))
app.add_page(department.add_page, route=routes.DEPARTMENT_ADD, on_load=protected_on_load(department_states.AddDepartmentState.on_load))
app.add_page(department.edit_page, route=routes.DEPARTMENT_EDIT+"[id]", on_load=protected_on_load(department_states.EditDepartmentState.on_load))
app.add_page(department.view_page, route=routes.DEPARTMENT_VIEW+"[id]", on_load=protected_on_load([department_states.ViewDepartmentState.on_load, AuditHistoryState.load("departments", Actions.DEPARTMENT_HISTORY_VIEW.value, Actions.DEPARTMENT_HISTORY_DETAIL.value)]))

app.add_page(speciality.list_page, route=routes.SPECIALITY_LIST, on_load=protected_on_load(speciality_states.ListSpecialityState.on_load))
app.add_page(speciality.add_page, route=routes.SPECIALITY_ADD, on_load=protected_on_load(speciality_states.AddSpecialityState.on_load))
app.add_page(speciality.edit_page, route=routes.SPECIALITY_EDIT+"[spec_id]", on_load=protected_on_load(speciality_states.EditSpecialityState.on_load))
app.add_page(speciality.view_page, route=routes.SPECIALITY_VIEW+"[spec_id]", on_load=protected_on_load([speciality_states.ViewSpecialityState.on_load, AuditHistoryState.load("specialties", Actions.SPECIALITY_HISTORY_VIEW.value, Actions.SPECIALITY_HISTORY_DETAIL.value, "spec_id")]))

app.add_page(application_status.list_page, route=routes.APPLICATION_STATUS_LIST, on_load=protected_on_load(application_status_states.ListApplicationStatusState.on_load))
app.add_page(application_status.add_page, route=routes.APPLICATION_STATUS_ADD, on_load=protected_on_load(application_status_states.AddApplicationStatusState.on_load))
app.add_page(application_status.edit_page, route=routes.APPLICATION_STATUS_EDIT+"[id]", on_load=protected_on_load(application_status_states.EditApplicationStatusState.on_load))
app.add_page(application_status.view_page, route=routes.APPLICATION_STATUS_VIEW+"[id]", on_load=protected_on_load([application_status_states.ViewApplicationStatusState.on_load, AuditHistoryState.load("application_statuses", Actions.APPLICATION_STATUS_HISTORY_VIEW.value, Actions.APPLICATION_STATUS_HISTORY_DETAIL.value)]))

app.add_page(role.list_page, route=routes.ROLES_LIST, on_load=protected_on_load(role_states.ListRoleState.on_load))
app.add_page(role.add_page, route=routes.ROLES_ADD, on_load=protected_on_load(role_states.AddRoleState.on_load))
app.add_page(role.edit_page, route=routes.ROLES_EDIT+"[id]", on_load=protected_on_load(role_states.EditRoleState.on_load))
app.add_page(role.view_page, route=routes.ROLES_VIEW+"[id]", on_load=protected_on_load([role_states.ViewRoleState.on_load, AuditHistoryState.load("roles", Actions.ROLE_HISTORY_VIEW.value, Actions.ROLE_HISTORY_DETAIL.value)]))

app.add_page(worker.list_page, route=routes.WORKERS_LIST, on_load=protected_on_load(worker_states.ListWorkerState.on_load))
app.add_page(worker.add_page, route=routes.WORKERS_ADD, on_load=protected_on_load(worker_states.AddWorkerState.on_load))
app.add_page(worker.edit_page, route=routes.WORKERS_EDIT+"[id]", on_load=protected_on_load(worker_states.EditWorkerState.on_load))
app.add_page(worker.view_page, route=routes.WORKERS_VIEW+"[id]", on_load=protected_on_load([worker_states.ViewWorkerState.on_load, AuditHistoryState.load("workers", Actions.WORKER_HISTORY_VIEW.value, Actions.WORKER_HISTORY_DETAIL.value)]))

app.add_page(item_zno.list_page, route=routes.ITEM_ZNO_LIST, on_load=protected_on_load(item_zno_states.ListItemZnoState.on_load))
app.add_page(item_zno.add_page, route=routes.ITEM_ZNO_ADD, on_load=protected_on_load(item_zno_states.AddItemZnoState.on_load))
app.add_page(item_zno.edit_page, route=routes.ITEM_ZNO_EDIT+"[id]", on_load=protected_on_load(item_zno_states.EditItemZnoState.on_load))
app.add_page(item_zno.view_page, route=routes.ITEM_ZNO_VIEW+"[id]", on_load=protected_on_load([item_zno_states.ViewItemZnoState.on_load, AuditHistoryState.load("item_zno", Actions.ITEM_ZNO_HISTORY_VIEW.value, Actions.ITEM_ZNO_HISTORY_DETAIL.value)]))

app.add_page(entry_base.list_page, route=routes.ENTRY_BASE_LIST, on_load=protected_on_load(entry_base_states.ListEntryBaseState.on_load))
app.add_page(entry_base.add_page, route=routes.ENTRY_BASE_ADD, on_load=protected_on_load(entry_base_states.AddEntryBaseState.on_load))
app.add_page(entry_base.edit_page, route=routes.ENTRY_BASE_EDIT+"[id]", on_load=protected_on_load(entry_base_states.EditEntryBaseState.on_load))
app.add_page(entry_base.view_page, route=routes.ENTRY_BASE_VIEW+"[id]", on_load=protected_on_load([entry_base_states.ViewEntryBaseState.on_load, AuditHistoryState.load("entry_base", Actions.ENTRY_BASE_HISTORY_VIEW.value, Actions.ENTRY_BASE_HISTORY_DETAIL.value)]))

app.add_page(form_of_study.list_page, route=routes.FORM_OF_STUDY_LIST, on_load=protected_on_load(form_of_study_states.ListFormOfStudyState.on_load))
app.add_page(form_of_study.add_page, route=routes.FORM_OF_STUDY_ADD, on_load=protected_on_load(form_of_study_states.AddFormOfStudyState.on_load))
app.add_page(form_of_study.edit_page, route=routes.FORM_OF_STUDY_EDIT+"[id]", on_load=protected_on_load(form_of_study_states.EditFormOfStudyState.on_load))
app.add_page(form_of_study.view_page, route=routes.FORM_OF_STUDY_VIEW+"[id]", on_load=protected_on_load([form_of_study_states.ViewFormOfStudyState.on_load, AuditHistoryState.load("forms_of_study", Actions.FORM_OF_STUDY_HISTORY_VIEW.value, Actions.FORM_OF_STUDY_HISTORY_DETAIL.value)]))

app.add_page(entrant_exam.list_page, route=routes.ENTRANT_EXAM_LIST, on_load=protected_on_load(entrant_exam_states.ListEntrantExamState.on_load))
app.add_page(entrant_exam.add_page, route=routes.ENTRANT_EXAM_ADD, on_load=protected_on_load(entrant_exam_states.AddEntrantExamState.on_load))
app.add_page(entrant_exam.edit_page, route=routes.ENTRANT_EXAM_EDIT+"[id]", on_load=protected_on_load(entrant_exam_states.EditEntrantExamState.on_load))
app.add_page(entrant_exam.view_page, route=routes.ENTRANT_EXAM_VIEW+"[id]", on_load=protected_on_load([entrant_exam_states.ViewEntrantExamState.on_load, AuditHistoryState.load("entrants_exams", Actions.ENTRANT_EXAM_HISTORY_VIEW.value, Actions.ENTRANT_EXAM_HISTORY_DETAIL.value)]))

app.add_page(entrants_group.list_page, route=routes.ENTRANTS_GROUP_LIST, on_load=protected_on_load(entrants_group_states.ListEntrantsGroupState.on_load))
app.add_page(entrants_group.auto_generate_page, route=routes.ENTRANTS_GROUP_AUTO, on_load=protected_on_load(entrants_group_states.AutoGenerateEntrantsGroupState.on_load))
app.add_page(entrants_group.print_page, route=routes.ENTRANTS_GROUP_PRINT, on_load=protected_on_load(entrants_group_states.PrintEntrantsGroupState.on_load))
app.add_page(entrants_group.add_page, route=routes.ENTRANTS_GROUP_ADD, on_load=protected_on_load(entrants_group_states.AddEntrantsGroupState.on_load))
app.add_page(entrants_group.edit_page, route=routes.ENTRANTS_GROUP_EDIT+"[id]", on_load=protected_on_load(entrants_group_states.EditEntrantsGroupState.on_load))
app.add_page(entrants_group.view_page, route=routes.ENTRANTS_GROUP_VIEW+"[id]", on_load=protected_on_load([entrants_group_states.ViewEntrantsGroupState.on_load, AuditHistoryState.load("entrants_groups", Actions.ENTRANTS_GROUP_HISTORY_VIEW.value, Actions.ENTRANTS_GROUP_HISTORY_DETAIL.value)]))

app.add_page(entrant.list_page, route=routes.ENTRANT_LIST, on_load=protected_on_load(entrant_states.ListEntrantState.on_load))
app.add_page(entrant.add_page, route=routes.ENTRANT_ADD, on_load=protected_on_load(entrant_states.EntrantFormState.on_load_add))
app.add_page(entrant.edit_page, route=routes.ENTRANT_EDIT+"[id]", on_load=protected_on_load(entrant_states.EntrantFormState.on_load_edit))
app.add_page(entrant.view_page, route=routes.ENTRANT_VIEW+"[id]", on_load=protected_on_load([entrant_states.ViewEntrantState.on_load, AuditHistoryState.load("entrants", Actions.ENTRANT_HISTORY_VIEW.value, Actions.ENTRANT_HISTORY_DETAIL.value)]))

app.add_page(entrant_application.list_page, route=routes.ENTRANT_APPLICATION_LIST, on_load=protected_on_load(entrant_application_states.ListEntrantApplicationState.on_load))

app.add_page(rating.list_page, route=routes.RATING_LIST, on_load=protected_on_load(rating_states.ListRatingState.on_load))

app.add_page(app_setting.list_page, route=routes.SETTINGS, on_load=protected_on_load(app_setting_states.ListAppSettingState.on_load))

app.add_page(admission_campaign.list_page, route=routes.ADMISSION_CAMPAIGN_LIST, on_load=protected_on_load(admission_campaign_states.ListAdmissionCampaignState.on_load))
app.add_page(admission_campaign.add_page, route=routes.ADMISSION_CAMPAIGN_ADD, on_load=protected_on_load(admission_campaign_states.AddAdmissionCampaignState.on_load))
app.add_page(admission_campaign.edit_page, route=routes.ADMISSION_CAMPAIGN_EDIT+"[id]", on_load=protected_on_load(admission_campaign_states.EditAdmissionCampaignState.on_load))
app.add_page(admission_campaign.view_page, route=routes.ADMISSION_CAMPAIGN_VIEW+"[id]", on_load=protected_on_load([admission_campaign_states.ViewAdmissionCampaignState.on_load, AuditHistoryState.load("admission_campaigns", Actions.ADMISSION_CAMPAIGN_HISTORY_VIEW.value, Actions.ADMISSION_CAMPAIGN_HISTORY_DETAIL.value)]))
