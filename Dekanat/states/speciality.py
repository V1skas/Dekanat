import reflex as rx

from typing import Sequence, Optional, List, Dict

from Dekanat.actions import Actions
from Dekanat import routes
from Dekanat.states.app import AppState

from Dekanat.models import SpecialityModel, DepartmentModel
from Dekanat.services.speciality import SpecialityService
from Dekanat.services.department import DepartmentService


class ListSpecialityState(AppState):
    items: Optional[Sequence[SpecialityModel]] = None
    in_progress: bool = True

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.SPECIALITY_LIST):
            yield rx.toast.error("У Вас немає дозволу на перегляд цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        try:
            self.in_progress = True

            service = SpecialityService()
            self.items = service.get_list_items()
            self.in_progress = False
            return
        except Exception:
            yield rx.toast.error("Під час виконання запиту сталася помилка :( Спробуйте знову.")
            return

    @rx.event
    def on_click_add(self):
        return rx.redirect(routes.SPECIALITY_ADD)


class AddSpecialityState(AppState):
    item: SpecialityModel = SpecialityModel()
    departments: Optional[Sequence[DepartmentModel]] = None
    in_process: bool = True

    def _reload_item(self):
        self.item = SpecialityModel()

    def _reload_departments(self):
        service = DepartmentService()
        self.departments = service.get_list_items()

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.SPECIALITY_ADD):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload_item()
            self._reload_departments()
            self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.var
    def department_options(self) -> List[Dict[str, str]]:
        if self.departments is None:
            return []
        return [{"value": str(d.id), "label": d.title} for d in self.departments]

    @rx.var
    def entity_code(self) -> str:
        return self.item.code if self.item is not None and self.item.code is not None else ""

    @rx.event
    def set_code(self, value: str):
        self.item.code = value

    @rx.var
    def id_department_str(self) -> str:
        if self.item is None or self.item.id_department is None or self.item.id_department == 0:
            return ""
        return str(self.item.id_department)

    @rx.event
    def set_id_department(self, value: str):
        try:
            self.item.id_department = int(value) if value else None  # type: ignore
        except (ValueError, TypeError):
            pass

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item is not None and self.item.title is not None else ""

    @rx.event
    def set_title(self, value: str):
        self.item.title = value

    @rx.var
    def tag(self) -> str:
        return self.item.tag if self.item is not None and self.item.tag is not None else ""

    @rx.event
    def set_tag(self, value: str):
        self.item.tag = value

    @rx.var
    def program(self) -> str:
        return self.item.educational_and_professional_program if self.item is not None and self.item.educational_and_professional_program is not None else ""

    @rx.event
    def set_program(self, value: str):
        self.item.educational_and_professional_program = value if value != "" else None  # type: ignore

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.SPECIALITY_ADD):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if not self.item.code or self.item.code == "":
            yield rx.toast.warning("Поле коду повинно бути заповненим!")
            return

        if self.item.id_department is None or self.item.id_department <= 0:
            yield rx.toast.warning("Оберіть відділення!")
            return

        if not self.item.title or self.item.title == "":
            yield rx.toast.warning("Поле назви повинно бути заповненим!")
            return

        if not self.item.tag or self.item.tag == "":
            yield rx.toast.warning("Поле тегу повинно бути заповненим!")
            return

        service = SpecialityService()
        try:
            self.item = service.add_one(self.item)
            yield rx.toast.success("Запис додано!")
            yield rx.redirect(f"{routes.SPECIALITY_VIEW}{self.item.id_department}/{self.item.code}")
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        return rx.redirect(routes.SPECIALITY_LIST)


class EditSpecialityState(AppState):
    item: SpecialityModel = SpecialityModel()
    in_process: bool = True

    def _reload_item(self):
        service = SpecialityService()
        code = str(self._route_param("spec_code", ""))
        try:
            id_department = int(self._route_param("dept_id", "-1"))
        except (ValueError, TypeError):
            id_department = -1
        loaded = service.get_by_pk(code, id_department)
        if loaded is not None:
            self.item = loaded

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.SPECIALITY_EDIT):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload_item()
            if self.item is None:
                yield rx.toast.warning("Запис не знайдено!")
                yield rx.redirect(routes.SPECIALITY_LIST)
                return
            self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.var
    def entity_code(self) -> str:
        return self.item.code if self.item is not None and self.item.code is not None else ""

    @rx.var
    def department_title(self) -> str:
        if self.item is not None and self.item.department is not None and self.item.department.title is not None:
            return self.item.department.title
        return ""

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item is not None and self.item.title is not None else ""

    @rx.event
    def set_title(self, value: str):
        self.item.title = value

    @rx.var
    def tag(self) -> str:
        return self.item.tag if self.item is not None and self.item.tag is not None else ""

    @rx.event
    def set_tag(self, value: str):
        self.item.tag = value

    @rx.var
    def program(self) -> str:
        return self.item.educational_and_professional_program if self.item is not None and self.item.educational_and_professional_program is not None else ""

    @rx.event
    def set_program(self, value: str):
        self.item.educational_and_professional_program = value if value != "" else None  # type: ignore

    @rx.event
    def on_save(self):
        if not self.has_permission(Actions.SPECIALITY_EDIT):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        if not self.item.title or self.item.title == "":
            yield rx.toast.warning("Поле назви повинно бути заповненим!")
            return

        if not self.item.tag or self.item.tag == "":
            yield rx.toast.warning("Поле тегу повинно бути заповненим!")
            return

        service = SpecialityService()
        try:
            self.item = service.edit_one(self.item)
            yield rx.toast.success("Запис змінено!")
            yield rx.redirect(f"{routes.SPECIALITY_VIEW}{self.item.id_department}/{self.item.code}")
        except Exception:
            yield rx.toast.error("Під час виконання запиту трапилась помилка. Спробуйте ще раз.")

    @rx.event
    def on_cancel(self):
        id_department = self._route_param("dept_id", "")
        code = self._route_param("spec_code", "")
        return rx.redirect(f"{routes.SPECIALITY_VIEW}{id_department}/{code}")


class ViewSpecialityState(AppState):
    item: SpecialityModel = SpecialityModel()
    in_process: bool = True

    def _reload_item(self):
        service = SpecialityService()
        code = str(self._route_param("spec_code", ""))
        try:
            id_department = int(self._route_param("dept_id", "-1"))
        except (ValueError, TypeError):
            id_department = -1
        loaded = service.get_by_pk(code, id_department)
        if loaded is not None:
            self.item = loaded

    @rx.event
    def on_load(self):
        if not self.has_permission(Actions.SPECIALITY_VIEW):
            yield rx.toast.error("У Вас немає доступу до цієї сторінки!")
            yield rx.redirect(routes.DASHBOARD)
            return

        self.in_process = True
        try:
            self._reload_item()
            if self.item is None:
                yield rx.toast.warning("Запис не знайдено!")
                yield rx.redirect(routes.DASHBOARD)
            else:
                self.in_process = False
        except Exception:
            yield rx.toast.error("Під час завантаження даних виникла помилка. Спробуйте ще раз.")
        return

    @rx.event
    def on_click_edit(self):
        if not self.has_permission(Actions.SPECIALITY_EDIT):
            return rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
        return rx.redirect(f"{routes.SPECIALITY_EDIT}{self.item.id_department}/{self.item.code}")

    @rx.event
    def on_click_delete(self):
        if not self.has_permission(Actions.SPECIALITY_DELETE):
            yield rx.toast.error("У Вас немає дозволу на виконання цієї дії!")
            return

        service = SpecialityService()
        if service.delete_one(self.item):
            yield rx.redirect(routes.SPECIALITY_LIST)
            yield rx.toast.success("Видалено!")
        else:
            yield rx.toast.error("Не вдалось видалити. Спробуйте ще раз.")
        return

    @rx.var
    def entity_code(self) -> str:
        return self.item.code if self.item is not None and self.item.code is not None else ""

    @rx.var
    def department_title(self) -> str:
        if self.item is not None and self.item.department is not None and self.item.department.title is not None:
            return self.item.department.title
        return ""

    @rx.var
    def title(self) -> str:
        return self.item.title if self.item is not None and self.item.title is not None else ""

    @rx.var
    def tag(self) -> str:
        return self.item.tag if self.item is not None and self.item.tag is not None else ""

    @rx.var
    def program(self) -> str:
        return self.item.educational_and_professional_program if self.item is not None and self.item.educational_and_professional_program is not None else ""
