
$(document).ready(function(){
    $('#submit').on('click',function(event){
         event.preventDefault();
         $.ajax({
            type: 'POST',
            url: "/contact/submit",
            headers: {
                "X-CSRFToken" : csrf,
                "Content-Type": "application/json"
            },
            data : JSON.stringify({ 
                name : $('#name').val(),
                email : $('#email').val(),
                link2  : $('#city').val(),
                message : $('#message').val(),
                }),
            dataType : 'json',
            contentType : 'application/json',
            success: function (e) {
                alert('Thanks for applying, '+$('#name').val()+'!');
                $('input').each(function(){$(this).val('');})
            },
            error: function (e) {
                alert('no');
            },
        });
    });
});
