function validate() {
    var isValid = true;

    $('textarea, input, select').each(function () {
      if ($(this).attr("type") !== 'email') {
        if ($(this).val() === '') {
          isValid = false;
          $(this).addClass("is-invalid")
        }
      } else if ($(this).val().indexOf("@") == -1) {
        alert("E-mail has to include @.")
        isValid = false;
        $(this).addClass("is-invalid")
      }

    });
    if (isValid) {
      isValid = confirm('Do you really want to submit the form?');
      if (isValid) { alert('The form was sent successfully!'); }
      else { alert('The form was not sent.'); }
      return isValid;
    } else {
      alert('Please fill out all the form!');
      return isValid;
    }
  }