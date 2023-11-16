var autoImageFn
var autoImageFn2
$(document).ready(function(){
    $('#appraisal').on('click',function(){      window.location.href='/appraisal';});
    $('#cityscore').on('click',function(){      window.location.href='/cityscore';    });
    $('#dealsheet').on('click',function(){      window.location.href='/dealsheet';    });
    if (window.location.href.includes('appraisal') ) { $('#appraisal').parent().css('background-color','#5ac'); } 
    if (window.location.href.includes('cityscore') ) { $('#cityscore').parent().css('background-color','#5ac'); } 
    if (window.location.href.includes('dealsheet') ) { $('#dealsheet').parent().css('background-color','#5ac'); } 

    // pro forma
    $("#addPartnerBtn").click(function() {
        // Clone the partner-row div and append it to the partnerList
        var partnerRow = $(".partner-row:first").clone();
        $("#partnerList").append(partnerRow);

        // Clear input values in the cloned row
        partnerRow.find('input').val('');
    });

    $('#generate').on('click',function(){
        $('.dealsheet_result').show();
    });
});
