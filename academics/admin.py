from django.contrib import admin
from django.contrib.auth.models import User
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportExportModelAdmin
from .models import Examination, StudentExam
from studentpage.models import Candidate
from django.utils.html import format_html
from django.db.models import Avg, Value
from django.db.models.functions import Cast, Replace
from django.db.models import FloatField
# ExamReports
from .models import ExaminationReport


class ExaminationReportResource(resources.ModelResource):
    class Meta:
        model = ExaminationReport
        fields = ('id', 'student_exam', 'candidate', 'teacher', 'speaking_score', 'listening_score',
                  'reading_score', 'writing_score', 'teachers_notes', 'way_forward', 'created_at', 'updated_at')


@admin.register(ExaminationReport)
class ExaminationReportAdmin(ImportExportModelAdmin):
    resource_class = ExaminationReportResource
    list_display = ('candidate', 'teacher', 'teachers_notes', 'way_forward', 'created_at', 'updated_at')
    list_filter = ('way_forward', 'teacher', 'created_at', 'updated_at')
    search_fields = (
    'candidate__First_Name', 'candidate__Last_Name', 'teacher__first_name', 'teacher__last_name', 'teachers_notes')
    date_hierarchy = 'created_at'
    list_per_page = 25

    fieldsets = (
        ('Examination Information', {
            'fields': ('student_exam', 'candidate', 'teacher'),
            'description': 'Basic information about the examination report.'
        }),
        ('Scores', {
            'fields': ('speaking_score', 'listening_score', 'reading_score', 'writing_score'),
            'description': 'Individual scores for each skill.',
            'classes': ('collapse',),
        }),
        ('Teacher\'s Evaluation', {
            'fields': ('teachers_notes', 'way_forward'),
            'description': 'Teacher\'s notes and decision on the way forward for the student.',
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': 'When the report was created and last updated.',
        }),
    )

    readonly_fields = ('created_at', 'updated_at')

    def display_scores(self, obj):
        scores = [
            f"Speaking: {obj.speaking_score}",
            f"Listening: {obj.listening_score}",
            f"Reading: {obj.reading_score}",
            f"Writing: {obj.writing_score}"
        ]
        return format_html("<br>".join(scores))

    display_scores.short_description = 'Scores'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('student_exam', 'candidate', 'teacher')
        return queryset

    def get_summary_metrics(self, request):
        queryset = self.get_queryset(request)
        avg_scores = queryset.aggregate(
            avg_speaking=Avg('speaking_score'),
            avg_listening=Avg('listening_score'),
            avg_reading=Avg('reading_score'),
            avg_writing=Avg('writing_score')
        )
        return {
            'total_reports': queryset.count(),
            'avg_scores': {k: f"{v:.2f}" if v else "N/A" for k, v in avg_scores.items()},
            'way_forward_counts': {k: queryset.filter(way_forward=k).count() for k, _ in
                                   ExaminationReport.WAY_FORWARD_CHOICES},
        }

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['summary_metrics'] = self.get_summary_metrics(request)
        return super().changelist_view(request, extra_context=extra_context)

    class Media:
        css = {
            'all': ('admin/css/examination_reports_admin.css',)
        }


class StudentExamResource(resources.ModelResource):
    student = fields.Field(
        column_name='student',
        attribute='student',
        widget=ForeignKeyWidget(Candidate, 'full_name')
    )
    name_of_exam = fields.Field(
        column_name='name_of_exam',
        attribute='name_of_exam',
        widget=ForeignKeyWidget(Examination, 'examination_name')
    )
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget(User, 'username')
    )

    class Meta:
        model = StudentExam
        fields = ('student', 'name_of_exam',
                  'speaking_score', 'speaking_total', 'listening_score', 'listening_total',
                  'reading_score', 'reading_total', 'writing_score', 'writing_total',
                  'percentage_score', 'missed_exam_reason', 'speaking_missed_reason',
                  'listening_missed_reason', 'reading_missed_reason', 'writing_missed_reason', 'user')
        export_order = fields

    def dehydrate_student(self, student_exam):
        return f"{student_exam.student.First_Name} {student_exam.student.Last_Name}"


@admin.register(Examination)
class ExaminationAdmin(admin.ModelAdmin):
    list_display = (
        'class_level', 'class_information', 'examination_name', 'date_added', 'user', 'student_count', 'average_score')
    list_filter = ('examination_name', 'class_information', 'class_level', 'date_added', 'user')
    search_fields = ('examination_name', 'class_information__course_class_no', 'user__username')
    date_hierarchy = 'date_added'

    def student_count(self, obj):
        return StudentExam.objects.filter(name_of_exam=obj).count()

    student_count.short_description = 'Number of Students'

    def average_score(self, obj):
        avg = StudentExam.objects.filter(name_of_exam=obj).exclude(percentage_score='').annotate(
            score_float=Cast(Replace('percentage_score', Value('%'), Value('')), FloatField())
        ).aggregate(avg_score=Avg('score_float'))['avg_score']
        return f"{avg:.2f}%" if avg is not None else "N/A"

    average_score.short_description = 'Average Score'


@admin.register(StudentExam)
class StudentExamAdmin(ImportExportModelAdmin):
    resource_class = StudentExamResource
    list_display = (
        'student', 'name_of_exam', 'display_scores_and_totals', 'percentage_score', 'display_missed_reasons',
        'overall_missed_reason', 'user')
    list_filter = ('student', 'name_of_exam', 'missed_exam_reason', 'user')
    search_fields = ('name_of_exam__examination_name', 'student__First_Name', 'student__Last_Name', 'user__username')

    fieldsets = (
        ('Exam Information', {
            'fields': ('name_of_exam', 'student', 'user')
        }),
        ('Overall Result', {
            'fields': ('percentage_score', 'missed_exam_reason'),
            'description': 'Overall exam result or reason for missing the entire exam.'
        }),
        ('Individual Scores and Totals', {
            'fields': (
                ('speaking_score', 'speaking_total', 'speaking_missed_reason'),
                ('listening_score', 'listening_total', 'listening_missed_reason'),
                ('reading_score', 'reading_total', 'reading_missed_reason'),
                ('writing_score', 'writing_total', 'writing_missed_reason')
            ),
            'description': 'Individual scores and totals for each skill or reasons for missing specific parts of the exam.'
        }),
    )

    def display_scores_and_totals(self, obj):
        scores_and_totals = [
            f"S: {obj.speaking_score}/{obj.speaking_total}" if obj.speaking_score is not None else "S: -/-",
            f"L: {obj.listening_score}/{obj.listening_total}" if obj.listening_score is not None else "L: -/-",
            f"R: {obj.reading_score}/{obj.reading_total}" if obj.reading_score is not None else "R: -/-",
            f"W: {obj.writing_score}/{obj.writing_total}" if obj.writing_score is not None else "W: -/-",
        ]
        return format_html("<br>".join(scores_and_totals))

    display_scores_and_totals.short_description = 'Scores/Totals'

    def display_missed_reasons(self, obj):
        reasons = [
            f"S: {obj.speaking_missed_reason}" if obj.speaking_missed_reason else "S: -",
            f"L: {obj.listening_missed_reason}" if obj.listening_missed_reason else "L: -",
            f"R: {obj.reading_missed_reason}" if obj.reading_missed_reason else "R: -",
            f"W: {obj.writing_missed_reason}" if obj.writing_missed_reason else "W: -",
        ]
        return format_html("<br>".join(reasons))

    display_missed_reasons.short_description = 'Individual Missed Reasons'

    def overall_missed_reason(self, obj):
        return obj.missed_exam_reason or '-'

    overall_missed_reason.short_description = 'Overall Missed Reason'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('name_of_exam', 'student', 'user')
        return queryset

    def get_summary_metrics(self, request):
        queryset = self.get_queryset(request)
        avg_score = queryset.exclude(percentage_score='').annotate(
            score_float=Cast(Replace('percentage_score', Value('%'), Value('')), FloatField())
        ).aggregate(avg_score=Avg('score_float'))['avg_score']

        return {
            'total_exams': queryset.count(),
            'avg_score': f"{avg_score:.2f}%" if avg_score is not None else "N/A",
            'missed_exams': queryset.exclude(missed_exam_reason='').count(),
        }

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['summary_metrics'] = self.get_summary_metrics(request)
        return super().changelist_view(request, extra_context=extra_context)

    class Media:
        css = {
            'all': ('admin/css/student_exam_admin.css',)
        }
