getNamesFromEmailsReady = false;
$(document).ready(function(){
    $('#getNamesFromEmails').on('click',function(){
        if (!getNamesFromEmailsReady) {
            alert('upload file first');
        } else {
            $('#result').html(response.emails);
        }
         });
    $('#uploadButton').on('click', function() {
        var fileInput = document.getElementById('fileInput');
        var file = fileInput.files[0];
        var formData = new FormData();
        formData.append('file', file);

        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/upload', true);
        xhr.onload = function () {
            if (xhr.status === 200) {
                // document.getElementById('result').innerHTML = xhr.responseText;
                response = JSON.parse(xhr.response);
                getNamesFromEmailsReady = true;
                $('#uploadComplete').text('☑ got '+response['count']+" lines");
                $('#getNamesFromEmails').text('Get result');
            } else {
                alert('er:'+xhr.statusText);
                console.error('Error:', xhr.statusText);
            }
        };
        xhr.send(formData);
    });
});

