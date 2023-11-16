var autoImageFn
var autoImageFn2
$(document).ready(function(){
    $('#appraisal').on('click',function(){      window.location.href='/appraisal';});
    $('#cityscore').on('click',function(){      window.location.href='/cityscore';    });
    $('#proforma').on('click',function(){      window.location.href='/proforma';    });
    if (window.location.href.includes('appraisal') ) { $('#appraisal').parent().css('background-color','#5ac'); } 
    if (window.location.href.includes('cityscore') ) { $('#cityscore').parent().css('background-color','#5ac'); } 
    if (window.location.href.includes('proforma') ) { $('#proforma').parent().css('background-color','#5ac'); } 
});
