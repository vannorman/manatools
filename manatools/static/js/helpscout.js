getNamesFromEmailsReady = false;
emailsResponse = null;
$(document).ready(function(){
    $('#getNamesFromEmails').on('click',function(){
        if (!getNamesFromEmailsReady) {
            alert('upload file first');
        } else {

             event.preventDefault();
             $.ajax({
                type: 'POST',
                url: "/convertEmails",
                headers: {
//                    "X-CSRFToken" : csrf,
                    "Content-Type": "application/json"
                },
                data : JSON.stringify({ 
                    emails : emailsResponse['emails'],
                    authorization : $('#AuthorizationHeader').val(),
                    }),
                dataType : 'json',
                contentType : 'application/json',
                success: function (data) {
                    console.log(data)
                    for (var i=0;i<data['items'].length;i++){
                        for (var j=0;j<data['items'][i].length;j++){
                            $('#result').append(data['items'][i][j]+",");
                        }
                        $('#result').append('<br>');
                    }
                },
                error: function (e) {
                    console.log('fail');
                },
            });
            console.log('fin click get');
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
                emailsResponse = JSON.parse(xhr.response); // bad global var
                getNamesFromEmailsReady = true;
                $('#uploadComplete').text('☑ got '+emailsResponse['count']+" lines");
                $('#getNamesFromEmails').text('Get result');
            } else {
                alert('er:'+xhr.statusText);
                console.error('Error:', xhr.statusText);
            }
        };
        xhr.send(formData);
    });
});

