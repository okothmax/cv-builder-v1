from django.urls import path
from . import views

urlpatterns = [
    path('select/exam/', views.existing_exams, name="existing_exams"),
    path('create-examination/', views.create_examination, name='create-examination'),
    path('exams/manage/<int:exam_id>/', views.manage_student_exams, name='manage_student_exams'),
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/edit/<int:exam_id>/', views.edit_exams, name='edit_exams'),
    path('exams/delete/<int:student_exam_id>/', views.delete_student_exam, name='delete_student_exam'),
    path('student/exams/<int:candidate_id>/', views.student_exam_result, name='student_exam_result'),
    path('class-numbers/', views.class_numbers, name='class_numbers'),
    path('update-scheduled-date/', views.update_scheduled_date, name='update_scheduled_date'),

    # reports
    path('class/assessments/', views.assessments_view, name='assessments_view'),
    path('present_examinations/', views.present_examinations, name='present_examinations'),
    path('students/exams/<int:exam_id>/', views.view_student_exams, name='view_student_exams'),
    path('admin-approve-report/<int:report_id>/', views.admin_approve_report, name='admin_approve_report'),
    # Exam
    path('filter-students-for-exam/<int:exam_id>/', views.filter_students_for_exam, name='filter_students_for_exam'),
    # Exam Reports on teachers' end
    path('exam-classes/', views.exam_class_numbers, name='exam_class_numbers'),
    path('reports/exam/', views.reports_existing_exams, name="reports_existing_exams"),


    path('filter-students-for-reports/<int:exam_id>/', views.filter_students_for_reports,
         name='filter_students_for_reports'),
    path('manage-examination-reports/<int:exam_id>/', views.manage_examination_reports,
         name='manage_examination_reports'),
    path('update-examination-report/<int:student_exam_id>/', views.update_examination_report,
         name='update_examination_report'),

    path('exams/<int:exam_id>/autosave/', views.autosave_exam_field, name='autosave_exam_field'),

]
