var autoImageFn
var autoImageFn2
$(document).ready(function(){
    $('#cityscore').on('click',function(){
        window.location.href='/cityscore';
    });
    $('input#city').cityAutocomplete();

});
