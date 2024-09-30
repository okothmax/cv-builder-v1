$(document).ready(function() {
    // Form navigation
    $(".next").click(function() {
        if(validateField($(this))) {
            nextSection($(this));
        }
    });

    $(".previous").click(function() {
        prevSection($(this));
    });

    // File upload handling
    $(".file-upload-button").click(function() {
        $("#profile-upload").click();
    });

    $("#profile-upload").change(function() {
        var fileName = $(this).val().split("\\").pop();
        $(".file-name").text(fileName || "No file chosen...");
        previewImage(this);
    });

    // Dynamic form fields
    $(".add-another").click(function() {
        var container = $(this).prev();
        var newEntry = container.children().first().clone();
        newEntry.find('input, textarea').val('');
        newEntry.append('<button type="button" class="delete-btn">Delete</button>');
        container.append(newEntry);
        updatePreview();
    });

    $(document).on('click', '.delete-btn', function() {
        $(this).parent().remove();
        updatePreview();
    });

    // Update preview on input
    $('form').on('input', 'input, textarea', function() {
        updatePreview();
    });

    // Initialize preview
    updatePreview();
});

function validateField(button) {
    var currentFieldset = button.parent();
    var inputs = currentFieldset.find('input[type="text"], input[type="email"], textarea').filter('[required]');
    var isValid = true;

    inputs.each(function() {
        if ($(this).val().trim() === "") {
            $(this).addClass('input-error');
            isValid = false;
        } else {
            $(this).removeClass('input-error');
        }
    });

    return isValid;
}

function nextSection(button) {
    var currentFieldset = button.parent();
    var nextFieldset = currentFieldset.next();

    currentFieldset.hide();
    nextFieldset.show();

    $("#progressbar li").eq($("fieldset").index(nextFieldset)).addClass("active");
}

function prevSection(button) {
    var currentFieldset = button.parent();
    var prevFieldset = currentFieldset.prev();

    currentFieldset.hide();
    prevFieldset.show();

    $("#progressbar li").eq($("fieldset").index(currentFieldset)).removeClass("active");
}

function previewImage(input) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.onload = function(e) {
            $('#cv-image').attr('src', e.target.result);
        }
        reader.readAsDataURL(input.files[0]);
    }
}

function updatePreview() {
    // Update personal information
    $('#resume .header h1').text($('input[name="firstname"]').val() + ' ' + $('input[name="lastname"]').val());
    $('#resume .header p').text($('input[name="email"]').val() + ' • ' + $('input[name="phone"]').val());

    // Update summary
    $('#resume .summary p').text($('textarea[name="summary"]').val());

    // Update work experience
    updateSectionPreview('work-experience', ['company', 'role', 'tenure', 'responsibilities']);

    // Update education
    updateSectionPreview('education', ['school', 'qualification', 'tenure']);

    // Update certifications
    updateSectionPreview('certification', ['certification']);

    // Update languages
    updateSectionPreview('language', ['language']);

    // Update skills
    updateSectionPreview('skill', ['skill']);

    // Update interests and hobbies
    updateSectionPreview('hobby', ['hobby']);

    // Update references
    updateSectionPreview('reference', ['Referees', 'Company', 'contact']);
}

function updateSectionPreview(sectionClass, fields) {
    var container = $('#resume .' + sectionClass);
    container.empty();

    $('.' + sectionClass + '-entry, .' + sectionClass + '-item').each(function() {
        var entry = $('<div></div>');
        fields.forEach(function(field) {
            var value = $(this).find('[name="' + field + '[]"]').val();
            if (value) {
                if (field === 'responsibilities') {
                    entry.append('<ul><li>' + value.split('\n').join('</li><li>') + '</li></ul>');
                } else {
                    entry.append('<p><strong>' + field.charAt(0).toUpperCase() + field.slice(1) + ':</strong> ' + value + '</p>');
                }
            }
        }.bind(this));
        container.append(entry);
    });
}