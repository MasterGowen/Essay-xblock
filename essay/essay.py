# -*- coding: utf-8 -*-

import datetime
import json
import logging
import pkg_resources

from xblock.core import XBlock
from xblock.fields import Boolean, DateTime, Scope, String, Integer
from xblock.fragment import Fragment
from xmodule.util.duedate import get_extended_due_date
log = logging.getLogger(__name__)


class Essay(XBlock):
    has_score = True
    icon_class = 'problem'

    display_name = String(
        default='Essay', scope=Scope.settings,
        help=u'Имя будет показано над этим блоком и в полосе навигации.'
    )

    points = Integer(
        display_name='Points count',
        values={"min": 0, "step": 1},
        default=10,
        scope=Scope.settings
    )

    score = Integer(
        display_name="Grade score",
        default=None,
        values={"min": 0, "step": 1},
        scope=Scope.user_state
    )

    comment = String(
        display_name="Instructor comment",
        default='',
        scope=Scope.user_state,
    )

    essay_timestamp = DateTime(
        display_name="Timestamp",
        scope=Scope.user_state,
        default=None
    )

    def max_score(self):
        return self.points

    def student_view(self, context=None):

        if not self.score_published:
            self.runtime.publish(self, 'grade', {
                'value': self.score,
                'max_value': self.max_score(),
            })
            self.score_published = True

        context = {
            "student_state": json.dumps(self.student_state()),
            "id": self.location.name.replace('.', '_')
        }

        fragment = Fragment()
        fragment.add_content(
            render_template(
                'templates/Essay/show.html',
                context
            )
        )
        fragment.add_css(_resource("static/css/essay.css"))
        fragment.add_javascript(_resource("static/js/essay.js"))
        fragment.initialize_js('Essay')
        return fragment

    def student_state(self):

        if self.score is not None:
            graded = {'score': self.score, 'comment': self.comment}
        else:
            graded = None

        return {
            "graded": graded,
            "max_score": self.max_score(),
        }

    def staff_grading_data(self):
        def get_student_data(module):
            state = json.loads(module.state)
            return {
                'module_id': module.id,
                'username': module.student.username,
                'fullname': module.student.profile.name,
                'timestamp': state.get("essay_timestamp"),
                'score': state.get("score"),
                'comment': state.get("comment", ''),
            }

        query = StudentModule.objects.filter(
            course_id=self.xmodule_runtime.course_id,
            module_state_key=self.location
        )

        return {
            'assignments': [get_student_data(module) for module in query],
            'max_score': self.max_score(),
        }

    def studio_view(self, context=None):
        try:
            cls = type(self)

            def none_to_empty(x):
                return x if x is not None else ''
            edit_fields = (
                (field, none_to_empty(getattr(self, field.name)), validator)
                for field, validator in (
                    (cls.display_name, 'string'),
                    (cls.points, 'number'))
            )

            context = {
                'fields': edit_fields
            }
            fragment = Fragment()
            fragment.add_content(
                render_template(
                    'templates/Essay/edit.html',
                    context
                )
            )
            fragment.add_javascript(_resource("static/js/studio.js"))
            fragment.initialize_js('Essay')
            return fragment
        except:  # pragma: NO COVER
            log.error("Not Essay", exc_info=True)
            raise