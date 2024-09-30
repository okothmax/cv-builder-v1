from django.shortcuts import render, redirect, get_object_or_404
from studentpage.models import Candidate
from django.contrib.auth.decorators import login_required
from .forms import StudentExamForm, ExaminationForm
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from decimal import Decimal, InvalidOperation

# New Reports Data
from teacherpage.models import Cohort, CourseIntake, Teacher
from .models import Examination, StudentExam, ExaminationReport
from django.db.models import Q, Exists, Subquery
from django.db.models import Count, OuterRef, F


@login_required(login_url='/teacher-login/')
def exam_class_numbers(request):
    if hasattr(request.user, 'teacher'):
        teacher = request.user.teacher
        cohorts = Cohort.objects.filter(teacher=teacher).order_by('course_class_no').select_related('course_intake')
        unique_class_numbers = [(cohort.course_class_no, str(cohort.course_intake)) for cohort in cohorts]
    else:
        unique_class_numbers = []

    context = {
        'unique_class_numbers': unique_class_numbers,
    }
    return render(request, 'exams_filter_with_class.html', context)


from .models import ScheduledExam


@login_required(login_url='/teacher-login/')
def reports_existing_exams(request):
    course_class_no = request.GET.get('course_class_no')
    if course_class_no:
        examinations = Examination.objects.filter(class_information__course_class_no=course_class_no)
    else:
        examinations = Examination.objects.all()

    exam_data = []
    for exam in examinations.select_related('class_information__teacher'):
        scheduled_exam = ScheduledExam.objects.filter(user=request.user, examination=exam).first()
        exam_data.append({
            'exam': exam,
            'scheduled_date': scheduled_exam.scheduled_date if scheduled_exam else None
        })

    context = {
        'exam_data': exam_data,
    }
    return render(request, 'reports_existing_exams.html', context)


@login_required(login_url='/teacher-login/')
def filter_students_for_reports(request, exam_id):
    examination = get_object_or_404(Examination, id=exam_id)
    course_class_no = request.GET.get('course_class_no')

    if not course_class_no:
        messages.error(request, "No class number provided. Please select a valid class number.")
        return redirect('exam_class_numbers')

    cohort = Cohort.objects.filter(course_class_no=course_class_no).first()

    time_choices = dict(Candidate._meta.get_field('Time').choices)
    current_time_filter = request.GET.get('time_filter')

    context = {
        'examination': examination,
        'cohort': cohort,
        'time_choices': time_choices,
        'current_time_filter': current_time_filter,
        'course_class_no': course_class_no,
    }

    if not cohort:
        messages.warning(request,
                         f"No cohort found with class number: {course_class_no}. Please select a valid class number.")
        return redirect('exam_class_numbers')
    elif current_time_filter:
        return redirect(reverse('manage_examination_reports', kwargs={'exam_id': exam_id}) +
                        f'?course_class_no={course_class_no}&time_filter={current_time_filter}')

    return render(request, 'filter_students_for_reports.html', context)


from django.http import JsonResponse
from .models import ClassReport


@login_required(login_url='/teacher-login/')
def manage_examination_reports(request, exam_id):
    examination = get_object_or_404(Examination, id=exam_id)
    course_class_no = request.GET.get('course_class_no') or request.POST.get('course_class_no')
    time_filter = request.GET.get('time_filter') or request.POST.get('time_filter')

    # Only redirect if it's a GET request and there's no time filter
    if request.method == "GET" and not time_filter:
        return redirect(reverse('filter_students_for_reports', kwargs={'exam_id': exam_id}) +
                        f'?course_class_no={course_class_no}')

    # Retrieve the current logged-in teacher's course location.
    teacher = get_object_or_404(Teacher, user=request.user)
    teacher_course_location = teacher.course_location

    cohorts = Cohort.objects.filter(course_class_no=course_class_no)

    if cohorts.exists():
        cohort = cohorts.first()
        students = Candidate.objects.filter(
            course_intake=cohort.course_intake,
            Time=time_filter,
            Course_Location=teacher_course_location
        )
    else:
        messages.error(request, f"No cohort found with class number: {course_class_no}")
        return redirect('exam_class_numbers')

    # Fetch all student exams for this examination and these students
    student_exams = StudentExam.objects.filter(
        name_of_exam=examination,
        student__in=students
    ).select_related('student', 'examination_report')

    if not student_exams.exists():
        messages.warning(request,
                         f"No student exams found for the given criteria: Class {course_class_no}, Time {time_filter}")
        return redirect(reverse('filter_students_for_reports', kwargs={'exam_id': exam_id}) +
                        f'?course_class_no={course_class_no}')

    # Get or create ExaminationReports for each StudentExam
    examination_reports = []
    for student_exam in student_exams:
        report, created = ExaminationReport.objects.get_or_create(
            student_exam=student_exam,
            candidate=student_exam.student,
            teacher=teacher
        )
        examination_reports.append(report)

    # Get or create ClassReport for this examination and cohort
    class_report, created = ClassReport.objects.get_or_create(
        examination=examination,
        cohort=cohort
    )

    if request.method == 'POST':
        if 'overall_report' in request.POST:
            # Handle the overall class report update
            overall_report = request.POST.get('overall_report', '').strip()
            class_report.overall_report = overall_report
            class_report.save()

            # Return JSON response for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Overall report updated successfully',
                })
        else:
            # Handle individual student report updates
            return update_examination_report(request, student_exams, examination_reports)

    context = {
        'examination': examination,
        'cohort': cohort,
        'student_exams': student_exams,
        'examination_reports': examination_reports,
        'way_forward_choices': ExaminationReport.WAY_FORWARD_CHOICES,
        'course_class_no': course_class_no,
        'time_filter': time_filter,
        'teacher': teacher,
        'class_report': class_report,  # Add class_report to the context
    }
    return render(request, 'manage_examination_reports.html', context)


from django.views.decorators.http import require_POST

from django.db import transaction


@require_POST
def update_examination_report(request, student_exam_id):
    try:
        with transaction.atomic():
            student_exam = get_object_or_404(StudentExam, id=student_exam_id)
            examination_report, created = ExaminationReport.objects.get_or_create(student_exam=student_exam)

            teachers_notes = request.POST.get('teachers_notes', '').strip()
            way_forward = request.POST.get('way_forward', '').strip()

            logger.info(f"Updating report for student_exam_id: {student_exam_id}")
            logger.info(f"Received teachers_notes: {teachers_notes}")
            logger.info(f"Received way_forward: {way_forward}")

            examination_report.teachers_notes = teachers_notes
            examination_report.way_forward = way_forward
            examination_report.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Examination report updated successfully',
        })
    except Exception as e:
        logger.exception(f"Error updating examination report for student_exam_id: {student_exam_id}")
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while updating the examination report'
        }, status=500)


def get_adjacent_levels(current_level):
    levels = ['A1.1', 'A1.2', 'A2.1', 'A2.2', 'B1.1', 'B1.2', 'B2.1', 'B2.2']
    if current_level not in levels:
        return None, None
    current_index = levels.index(current_level)
    previous_level = levels[current_index - 1] if current_index > 0 else None
    next_level = levels[current_index + 1] if current_index < len(levels) - 1 else None
    return previous_level, next_level


def assessments_view(request):
    # Start with all cohorts that have examinations
    cohorts = Cohort.objects.filter(examination__isnull=False).distinct().select_related(
        'teacher', 'course_intake'
    ).annotate(
        student_count=Count('examination__studentexam', distinct=True),
    )

    # Apply filters
    filter_params = Q()
    if 'course_location' in request.GET:
        filter_params &= Q(teacher__course_location=request.GET['course_location'])
    if 'teacher' in request.GET:
        filter_params &= Q(teacher__id=request.GET['teacher'])
    if 'class_time' in request.GET:
        filter_params &= Q(course_intake__course_intake__icontains=request.GET['class_time'])

    cohorts = cohorts.filter(filter_params)

    # Get unique values for filter fields
    unique_locations = Teacher.objects.filter(cohort__in=cohorts).values_list('course_location', flat=True).distinct()
    unique_teachers = Teacher.objects.filter(cohort__in=cohorts).values('id', 'first_name', 'last_name').distinct()

    # Get unique class times
    unique_class_times = Candidate.objects.filter(
        course_intake__in=CourseIntake.objects.filter(
            cohort__in=cohorts
        ).values_list('course_intake', flat=True)
    ).values_list('Time', flat=True).distinct()

    levels = ['A1.1', 'A1.2', 'A2.1', 'A2.2', 'B1.1', 'B1.2', 'B2.1', 'B2.2']

    # Prepare data for template
    cohorts_data = []
    for cohort in cohorts:
        # Get the most common time for this cohort
        common_time = Candidate.objects.filter(
            course_intake=cohort.course_intake.course_intake
        ).values('Time').annotate(
            count=Count('Time')
        ).order_by('-count').first()

        # Get all non-custom examinations for this cohort with actual student exam entries
        exams_with_scores = Examination.objects.filter(
            class_information=cohort,
            class_level__in=levels
        ).annotate(
            has_scores=Exists(StudentExam.objects.filter(name_of_exam=OuterRef('pk')))
        ).filter(has_scores=True).order_by('class_level')

        if exams_with_scores.exists():
            exam_levels = list(exams_with_scores.values_list('class_level', flat=True))

            # Find the highest level exam with scores
            highest_level = max(exam_levels, key=lambda x: levels.index(x))

            # Determine previous and next exam levels
            current_index = levels.index(highest_level)
            previous_level = next((level for level in reversed(levels[:current_index]) if level in exam_levels), "N/A")
            next_level = next((level for level in levels[current_index + 1:] if level not in exam_levels), "N/A")

            current_level = highest_level
        else:
            current_level, previous_level, next_level = "N/A", "N/A", "N/A"

        cohorts_data.append({
            'class_no': cohort.course_class_no,
            'class_information': f"{cohort.course_class_no} - {cohort.course_intake.course_intake}",
            'teacher': f"{cohort.teacher.first_name} {cohort.teacher.last_name}",
            'student_count': cohort.student_count,
            'location': cohort.teacher.course_location,
            'class_time': common_time['Time'] if common_time else "N/A",
            'current_level': current_level,
            'previous_exam': previous_level,
            'next_exam': next_level,
        })

    active_filters = {k: v for k, v in request.GET.items() if k in ['course_location', 'teacher', 'class_time'] and v}

    context = {
        'cohorts_data': cohorts_data,
        'unique_locations': sorted(unique_locations),
        'unique_teachers': unique_teachers,
        'unique_class_times': sorted(unique_class_times),
        'active_filters': active_filters,
    }
    return render(request, 'assessments.html', context)


def present_examinations(request):
    classinfo = []
    course_class_no = request.GET.get('course_class_no')

    if course_class_no:
        classinfo = Examination.objects.filter(class_information__course_class_no=course_class_no)
    else:
        classinfo = Examination.objects.all()

    for exam in classinfo:
        # Add teacher information
        exam.teacher = exam.class_information.teacher if exam.class_information else None

        # Date scheduled (placeholder for now)
        exam.date_scheduled = "TBS"

        # Date entered (using the date_added field from Examination model)
        exam.date_entered = exam.date_added.strftime("%A, %B %d, %Y")

        # Calculate pass rate
        total_students = StudentExam.objects.filter(name_of_exam=exam).count()
        passed_students = StudentExam.objects.filter(name_of_exam=exam, percentage_score__gte='60%').count()

        if total_students > 0:
            pass_rate = (passed_students / total_students) * 100
            exam.pass_rate = f"{passed_students}/{total_students}"

            if pass_rate >= 80:
                exam.pass_rate_class = "pass-rate-high"
            elif pass_rate >= 60:
                exam.pass_rate_class = "pass-rate-medium"
            else:
                exam.pass_rate_class = "pass-rate-low"
        else:
            exam.pass_rate = "0/0"
            exam.pass_rate_class = "pass-rate-none"

        # Calculate participation rate
        total_class_students = Candidate.objects.filter(course_intake=exam.class_information.course_intake).count()

        if total_class_students > 0:
            participation_rate = (total_students / total_class_students) * 100
            exam.participation_rate = f"{total_students}/{total_class_students}"

            if participation_rate >= 90:
                exam.participation_class = "participation-high"
            elif participation_rate >= 75:
                exam.participation_class = "participation-medium"
            else:
                exam.participation_class = "participation-low"
        else:
            exam.participation_rate = "0/0"
            exam.participation_class = "participation-none"

    context = {
        'classinfo': classinfo,
    }
    return render(request, 'report_exams.html', context)


from django.db.models import Prefetch


def view_student_exams(request, exam_id):
    examination = get_object_or_404(Examination.objects.select_related('class_information__teacher'), id=exam_id)
    exam_name = examination.examination_name or examination.class_level
    course_class_no = request.GET.get('course_class_no') or request.POST.get('course_class_no')

    cohorts = Cohort.objects.filter(course_class_no=course_class_no)

    if cohorts.exists():
        cohort = cohorts.first()
        students = Candidate.objects.filter(course_intake=cohort.course_intake)
        exams = StudentExam.objects.filter(
            name_of_exam_id=examination.id,
            student__course_intake=cohort.course_intake
        ).select_related('student').prefetch_related(
            Prefetch('examination_report', queryset=ExaminationReport.objects.all(), to_attr='report')
        ).annotate(
            speaking_display=F('speaking_score'),
            listening_display=F('listening_score'),
            reading_display=F('reading_score'),
            writing_display=F('writing_score')
        )
    else:
        cohort = None
        students = []
        exams = []
        if course_class_no:
            messages.error(request, f"No cohort found with class number: {course_class_no}")

    context = {
        'examination': examination,
        'exam_name': exam_name,
        'students': students,
        'cohort': cohort,
        'exams': exams,
        'way_forward_choices': ExaminationReport.WAY_FORWARD_CHOICES,
    }

    return render(request, 'viewing_exams.html', context)


from django.utils import timezone


def admin_approve_report(request, report_id):
    if request.method == 'POST':
        report = get_object_or_404(ExaminationReport, id=report_id)
        decision = request.POST.get('admin_decision')
        notes = request.POST.get('admin_notes')

        if decision in ['approve', 'reject']:
            report.admin_decision = 'approved' if decision == 'approve' else 'rejected'
            report.admin_notes = notes
            report.admin_decision_date = timezone.now()
            report.save()

        return redirect('view_student_exams', exam_id=report.student_exam.name_of_exam.id)

    # If not a POST request, redirect to the same view_student_exams URL
    report = get_object_or_404(ExaminationReport, id=report_id)
    return redirect('view_student_exams', exam_id=report.student_exam.name_of_exam.id)


@login_required(login_url='login')
def student_exam_result(request, candidate_id):
    candidate = get_object_or_404(Candidate, pk=candidate_id)
    if hasattr(request.user, 'candidate'):
        candidate = request.user.candidate

    exams = StudentExam.objects.filter(student=candidate)

    context = {
        'candidate': candidate,
        'exams': exams,
        'skills': ['speaking', 'listening', 'reading', 'writing'],
    }

    return render(request, 'students_viewing_exams.html', context)


@login_required
def exam_list(request):
    exams = Examination.objects.filter(user=request.user)
    return render(request, 'exams_list.html', {'exams': exams})


@login_required
def edit_exams(request, exam_id):
    examination = get_object_or_404(Examination, id=exam_id, user=request.user)
    student_exams = StudentExam.objects.filter(name_of_exam=examination)
    missed_assessment_reasons_choices = StudentExam._meta.get_field('missed_exam_reason').choices

    if request.method == 'POST':
        for student_exam in student_exams:
            score_key = f'score_{student_exam.id}'
            reason_key = f'reason_{student_exam.id}'

            percentage_score = request.POST.get(score_key, '').strip()
            missed_exam_reason = request.POST.get(reason_key, '').strip()

            # Update the student_exam record
            if percentage_score:
                student_exam.percentage_score = percentage_score
            if missed_exam_reason:
                student_exam.missed_exam_reason = missed_exam_reason

            student_exam.save()

        messages.success(request, "Exam records updated successfully!")
        return redirect('exam_list')  # Assuming 'exam_list' is the name of your exam listing view

    context = {
        'examination': examination,
        'student_exams': student_exams,
        'missed_assessment_reasons_choices': missed_assessment_reasons_choices,
    }
    return render(request, 'edit_exams.html', context)


@login_required
def delete_student_exam(request, student_exam_id):
    student_exam = get_object_or_404(StudentExam, id=student_exam_id)
    exam_id = student_exam.name_of_exam.id
    course_class_no = request.GET.get('course_class_no') or request.POST.get('course_class_no')

    student_exam.delete()

    # Preparing the redirection URL
    redirect_url = reverse('manage_student_exams', kwargs={'exam_id': exam_id})
    if course_class_no:
        redirect_url += f'?course_class_no={course_class_no}'

    return HttpResponseRedirect(redirect_url)


import logging

logger = logging.getLogger(__name__)

from django.db.models import Subquery
@login_required(login_url='/teacher-login/')
def manage_student_exams(request, exam_id):
    examination = get_object_or_404(Examination, id=exam_id)
    course_class_no = request.GET.get('course_class_no') or request.POST.get('course_class_no')
    cohorts = Cohort.objects.filter(course_class_no=course_class_no)
    time_filter = request.GET.get('time_filter') or request.POST.get('time_filter')

    # Only redirect if it's a GET request and there's no time filter
    if request.method == "GET" and not time_filter:
        return redirect(reverse('filter_students_for_exam', kwargs={'exam_id': exam_id}) +
                        f'?course_class_no={course_class_no}')

    # Retrieve the current logged-in teacher's course location.
    teacher_course_location = None
    if request.user.is_authenticated and hasattr(request.user, 'teacher'):
        teacher_course_location = request.user.teacher.course_location

    if cohorts.exists():
        cohort = cohorts.first()
        students = Candidate.objects.filter(course_intake=cohort.course_intake)
        if time_filter:
            students = students.filter(
                Time=time_filter,
                Course_Location=teacher_course_location
            )

        # Annotate students with their exam data
        students = students.annotate(
            student_exam_id=Subquery(
                StudentExam.objects.filter(
                    name_of_exam=examination,
                    student=OuterRef('pk')
                ).values('id')[:1]
            )
        )
    else:
        cohort = None
        students = []
        if course_class_no:
            messages.error(request, f"No cohort found with class number: {course_class_no}")

    missed_assessment_reasons = StudentExam._meta.get_field('missed_exam_reason').choices

    if request.method == "POST":
        # NEW: Handle autosave AJAX requests
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            student_id = request.POST.get('student_id')
            skill = request.POST.get('skill')
            score = request.POST.get('score')
            total = request.POST.get('total')
            missed_reason = request.POST.get('missed_reason')

            student = get_object_or_404(Candidate, id=student_id)
            student_exam, created = StudentExam.objects.get_or_create(
                name_of_exam=examination,
                student=student,
                defaults={'user': request.user}
            )

            # Update the specific skill fields
            setattr(student_exam, f'{skill}_score', Decimal(score) if score else None)
            setattr(student_exam, f'{skill}_total', Decimal(total) if total else None)
            setattr(student_exam, f'{skill}_missed_reason', missed_reason if missed_reason else None)

            student_exam.save()

            # Recalculate percentage score
            student_exam.calculate_and_save_percentage_score()

            # Determine failed assessments
            failed_assessments = [s for s in ['speaking', 'listening', 'reading', 'writing']
                                  if getattr(student_exam, f'{s}_score') and
                                  getattr(student_exam, f'{s}_total') and
                                  float(getattr(student_exam, f'{s}_score')) < 0.6 * float(getattr(student_exam, f'{s}_total'))]

            return JsonResponse({
                'success': True,
                'percentage_score': student_exam.percentage_score,
                'failed_assessments': failed_assessments
            })

        # Existing POST handling code
        save_all = request.POST.get('save_all') == 'true'
        student_ids = [request.POST.get(f'student_id_{i}') for i in range(len(students))] if save_all else [
            request.GET.get('student_id')]

        # Store global totals from the POST request
        global_totals = {skill: request.POST.get(f'{skill}_total', '') for skill in
                         ['speaking', 'listening', 'reading', 'writing']}
        request.session['global_totals'] = global_totals

        any_changes = False
        for student_id in student_ids:
            if student_id:
                student = get_object_or_404(Candidate, id=student_id)
                student_exam, created = StudentExam.objects.get_or_create(
                    name_of_exam=examination,
                    student=student,
                    defaults={'user': request.user}
                )

                changes = {}
                errors = []
                valid_scores = []

                for skill in ['speaking', 'listening', 'reading', 'writing']:
                    score = request.POST.get(f'{skill}_score_{student_id}', '').strip()
                    total = request.POST.get(f'{skill}_total_{student_id}', '').strip() or global_totals.get(skill, '')
                    reason = request.POST.get(f'{skill}_missed_reason_{student_id}', '').strip()

                    logger.debug(
                        f"Processing {skill} for student {student_id}: score={score}, total={total}, reason={reason}")

                    if score or total:
                        try:
                            score_decimal = Decimal(score) if score else Decimal('0')
                            total_decimal = Decimal(total) if total else None

                            if total_decimal is None or total_decimal <= 0:
                                errors.append(f"{skill.capitalize()} total must be greater than 0.")
                            elif score_decimal > total_decimal:
                                errors.append(f"{skill.capitalize()} score cannot be greater than the total.")
                            else:
                                percentage = (score_decimal / total_decimal) * 100
                                changes[f'{skill}_score'] = score_decimal
                                changes[f'{skill}_total'] = total_decimal
                                changes[f'{skill}_missed_reason'] = ''
                                valid_scores.append(percentage)
                        except InvalidOperation:
                            errors.append(f"Invalid {skill} score or total entered. Please enter valid numbers.")
                    elif reason:
                        changes[f'{skill}_missed_reason'] = reason
                        changes[f'{skill}_score'] = None
                        changes[f'{skill}_total'] = None
                    else:
                        # If all fields are empty, don't change anything
                        pass

                # Calculate overall percentage score
                if valid_scores:
                    overall_score = sum(valid_scores) / len(valid_scores)
                    changes['percentage_score'] = f"{overall_score:.2f}%"
                    changes['missed_exam_reason'] = ''
                elif 'missed_exam_reason' in request.POST:
                    overall_reason = request.POST.get('missed_exam_reason', '').strip()
                    if overall_reason:
                        changes['percentage_score'] = ''
                        changes['missed_exam_reason'] = overall_reason
                    else:
                        # If no valid scores and no overall reason, don't change overall fields
                        pass

                logger.debug(f"Changes for student {student_id}: {changes}")
                logger.debug(f"Errors for student {student_id}: {errors}")

                # Update and save the student exam instance
                if changes:
                    for field, value in changes.items():
                        setattr(student_exam, field, value)
                    try:
                        student_exam.save()
                        any_changes = True
                        if not save_all:
                            messages.success(request,
                                             f"Examination record for student {student.First_Name} {student.Last_Name} updated successfully.")
                    except Exception as e:
                        logger.exception(f"Error saving data for student {student_id}")
                        errors.append(f"Error saving data: {str(e)}")

                if errors:
                    for error in errors:
                        messages.error(request, f"Error for {student.First_Name} {student.Last_Name}: {error}")
                elif not changes and not save_all:
                    messages.info(request,
                                  f"No changes were made for student {student.First_Name} {student.Last_Name}.")

        if save_all:
            if any_changes:
                messages.success(request, "All examination records updated successfully.")
            else:
                messages.info(request, "No changes were made to any examination records.")

        # Redirect to manage student exams page
        redirect_url = reverse('manage_student_exams', kwargs={'exam_id': exam_id})
        if course_class_no:
            redirect_url += f'?course_class_no={course_class_no}'
        return redirect(redirect_url)

    # For GET requests, retrieve global totals from session or initialize empty
    global_totals = request.session.get('global_totals', {})
    if not global_totals:
        global_totals = {skill: '' for skill in ['speaking', 'listening', 'reading', 'writing']}
        request.session['global_totals'] = global_totals

    # Modify this part to create a dictionary of examination reports
    student_exams = StudentExam.objects.filter(
        id__in=[student.student_exam_id for student in students if student.student_exam_id]
    ).select_related('student')
    examination_reports = ExaminationReport.objects.filter(
        student_exam__in=student_exams
    ).select_related('student_exam')

    # Create a dictionary of examination reports keyed by student_exam_id
    examination_reports_dict = {report.student_exam_id: report for report in examination_reports}

    # Create a dictionary of student exams keyed by student_id
    student_exams_dict = {exam.student_id: exam for exam in student_exams}

    # Create a dictionary to store whether each student has passed
    students_passed_dict = {}

    for student_exam in student_exams:
        all_scores_above_60 = all(
            float(getattr(student_exam, f'{skill}_score', 0) or 0) >=
            0.6 * float(getattr(student_exam, f'{skill}_total', 1) or 1)
            for skill in ['speaking', 'listening', 'reading', 'writing']
        )
        students_passed_dict[student_exam.student_id] = all_scores_above_60

    # Create admin_decisions_dict (if not already created)
    admin_decisions_dict = {report.student_exam.student_id: report.admin_decision
                            for report in examination_reports}

    context = {
        'examination': examination,
        'students': students,
        'cohort': cohort,
        'missed_assessment_reasons': missed_assessment_reasons,
        'skills': ['speaking', 'listening', 'reading', 'writing'],
        'time_choices': dict(Candidate._meta.get_field('Time').choices),
        'current_time_filter': time_filter,
        'global_totals': global_totals,
        # ... Reports ...
        'examination_reports_dict': examination_reports_dict,
        'student_exams_dict': student_exams_dict,
        'way_forward_choices': ExaminationReport.WAY_FORWARD_CHOICES,
        'admin_decisions_dict': admin_decisions_dict,
        'students_passed_dict': students_passed_dict,  # Add this line
    }

    return render(request, 'posting_exams.html', context)


@login_required
@require_POST
def autosave_exam_field(request, exam_id):
    examination = get_object_or_404(Examination, id=exam_id)
    student_id = request.POST.get('student_id')
    skill = request.POST.get('skill')
    field_type = request.POST.get('field_type')
    value = request.POST.get('value')

    try:
        student_exam, created = StudentExam.objects.get_or_create(
            name_of_exam=examination,
            student_id=student_id,
            defaults={'user': request.user}
        )

        if field_type == 'score':
            setattr(student_exam, f'{skill}_score', value)
        elif field_type == 'total':
            setattr(student_exam, f'{skill}_total', value)
        elif field_type == 'missed_reason':
            setattr(student_exam, f'{skill}_missed_reason', value)

        student_exam.save()

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# Filter students exam
@login_required(login_url='/teacher-login/')
def filter_students_for_exam(request, exam_id):
    # Fetch the examination object
    examination = get_object_or_404(Examination, id=exam_id)

    # Get the course class number from the query parameters
    course_class_no = request.GET.get('course_class_no')

    # Fetch the cohort based on the course class number
    cohort = Cohort.objects.filter(course_class_no=course_class_no).first()

    if not cohort:
        messages.error(request, f"No cohort found with class number: {course_class_no}")
        # Redirect to an appropriate page if cohort is not found
        return redirect('some_error_page')

    # Define time choices
    time_choices = dict(Candidate._meta.get_field('Time').choices)

    # Check if a time filter is already applied (for example, if user is returning to this page)
    current_time_filter = request.GET.get('time_filter')

    context = {
        'examination': examination,
        'cohort': cohort,
        'time_choices': time_choices,
        'current_time_filter': current_time_filter,
    }

    # If a time filter is already selected, redirect to manage_student_exams view
    if current_time_filter:
        return redirect(reverse('manage_student_exams', kwargs={'exam_id': exam_id}) +
                        f'?course_class_no={course_class_no}&time_filter={current_time_filter}')

    return render(request, 'filter_students_for_exam.html', context)


@login_required(login_url='/teacher-login/')
def create_examination(request):
    if request.method == 'POST':
        form = ExaminationForm(request.POST)
        if form.is_valid():
            examination = form.save(commit=False)
            examination.user = request.user
            examination.save()
            return redirect('class_numbers')
    else:
        form = ExaminationForm(user=request.user)

    return render(request, 'creating_exams.html', {'form': form})


@login_required(login_url='/teacher-login/')
def existing_exams(request):
    course_class_no = request.GET.get('course_class_no')

    if course_class_no:
        exams = Examination.objects.filter(class_information__course_class_no=course_class_no)
    else:
        exams = Examination.objects.all()

    exam_data = []
    for exam in exams.select_related('class_information__teacher'):
        scheduled_exam = ScheduledExam.objects.filter(user=request.user, examination=exam).first()
        exam_data.append({
            'exam': exam,
            'scheduled_date': scheduled_exam.scheduled_date if scheduled_exam else None
        })

    context = {
        'exam_data': exam_data,
    }

    return render(request, 'existing_exams.html', context)


from django.utils.dateparse import parse_datetime
from django.utils import timezone

logger = logging.getLogger(__name__)


@login_required
@require_POST
def update_scheduled_date(request):
    exam_id = request.POST.get('exam_id')
    scheduled_date = request.POST.get('scheduled_date')

    if not exam_id or not scheduled_date:
        return JsonResponse({'status': 'error', 'message': 'Missing required data'}, status=400)

    try:
        examination = Examination.objects.get(id=exam_id)
        scheduled_exam, created = ScheduledExam.objects.get_or_create(
            user=request.user,
            examination=examination,
            defaults={'scheduled_date': timezone.now()}  # Provide a default value
        )

        # Parse the datetime and make it timezone-aware
        parsed_date = parse_datetime(scheduled_date)
        if parsed_date is not None:
            aware_datetime = timezone.make_aware(parsed_date, timezone.get_current_timezone())
            scheduled_exam.scheduled_date = aware_datetime
            scheduled_exam.save()
            return JsonResponse({'status': 'success', 'message': 'Date updated successfully'})
        else:
            logger.warning(f"Invalid date format received: {scheduled_date}")
            return JsonResponse({'status': 'error', 'message': 'Invalid date format'}, status=400)
    except Examination.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Examination not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in update_scheduled_date: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred'}, status=500)


@login_required(login_url='/teacher-login/')
def class_numbers(request):
    if hasattr(request.user, 'teacher'):
        teacher = request.user.teacher
        cohorts = Cohort.objects.filter(teacher=teacher).order_by('course_class_no').select_related('course_intake')
        unique_class_numbers = [(cohort.course_class_no, str(cohort.course_intake)) for cohort in cohorts]
    else:
        unique_class_numbers = []

    context = {
        'unique_class_numbers': unique_class_numbers,
    }
    return render(request, 'filter_with_class.html', context)
