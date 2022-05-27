import os
import pickle
from typing import List

from requests import Session

from PyYandexLMS.errors import AuthError
from PyYandexLMS.models.lesson import BaseLesson, Lesson
from PyYandexLMS.models.task import TaskType, Task
from PyYandexLMS.models.user import User


class Client(Session):
    def __init__(self, login, password, session_name=None):
        super().__init__()
        session_name = session_name or f"{login}.session"
        if not os.path.exists(session_name):
            if (
                self.post(
                    "https://passport.yandex.ru/passport?mode=auth",
                    data={"login": login, "passwd": password},
                ).url
                != "https://passport.yandex.ru/profile"
            ):
                raise AuthError("Ошибка авторизации (Неверные данные или включен 2FA)")
            with open(session_name, "wb") as f:
                pickle.dump(self.cookies, f)
        else:
            with open(session_name, "rb") as f:
                self.cookies = pickle.load(f)

    def check_authorized(self):
        """Проверка авторизации пользователя"""
        return self.get("https://api.passport.yandex.ru/all_accounts").text != "{}"

    def get_user(
        self,
        with_courses_summary: bool = True,
        with_expelled: bool = True,
        with_children: bool = True,
        with_parents: bool = True,
    ) -> User:
        """
        Возвращает информацию о пользователе в виде объекта User.

        :param with_courses_summary: Получить информацию о курсах пользователя
        :param with_expelled: Включить информацию о законченных курсах
        :param with_children: Показать информацию о детях (Если пользователь - родитель)
        :param with_parents: Показать информацию о родителях (Если пользователь - ребенок)
        """
        return User.parse_obj(
            self.get(
                "https://lyceum.yandex.ru/api/profile",
                params={
                    "withCoursesSummary": str(with_courses_summary).lower(),
                    "withExpelled": str(with_expelled).lower(),
                    "withChildren": str(with_children).lower(),
                    "withParents": str(with_parents).lower(),
                },
            ).json()
        )

    def get_lessons(self, course_id, group_id) -> List[BaseLesson]:
        """
        Возвращает список уроков в курсе.

        :param course_id: Идентификатор курса
        :param group_id: Идентификатор группы
        """
        lessons = self.get(
            "https://lyceum.yandex.ru/api/student/lessons/",
            params={"courseId": course_id, "groupId": group_id},
        ).json()
        return [BaseLesson.parse_obj(lesson) for lesson in lessons]

    def get_lesson(self, lesson_id, course_id, group_id) -> Lesson:
        """
        Возвращает информацию о уроке.

        :param lesson_id: Идентификатор урока
        :param course_id: Идентификатор курса
        :param group_id: Идентификатор группы
        """
        return Lesson.parse_obj(
            self.get(
                f"https://lyceum.yandex.ru/api/student/lessons/{lesson_id}",
                params={"courseId": course_id, "groupId": group_id},
            ).json()
        )

    def get_tasks(self, lesson_id, course_id, group_id) -> List[TaskType]:
        """
        Возвращает список заданий в уроке.

        :param lesson_id: Идентификатор урока
        :param course_id: Идентификатор курса
        :param group_id: Идентификатор группы
        """
        tasks = self.get(
            "https://lyceum.yandex.ru/api/student/lessonTasks",
            params={"courseId": course_id, "groupId": group_id, "lessonId": lesson_id},
        ).json()
        return [TaskType.parse_obj(task_type) for task_type in tasks]

    def get_task(self, task_id, group_id) -> Task:
        """
        Возвращает информацию о задании.

        :param task_id: Идентификатор задания
        :param group_id: Идентификатор группы
        """
        return Task.parse_obj(
            self.get(
                f"https://lyceum.yandex.ru/api/student/tasks/{task_id}",
                params={"groupId": group_id},
            ).json()
        )
