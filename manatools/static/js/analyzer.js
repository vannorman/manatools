$(document).ready(function(){
    /* flow:
        user submits list of csv addresses
        python ingests via analyzer/submit fn,
        pulls each address from csv,
        for each address,
            gets address to gps, 
            uses maps street view api to get image(s), 
            zips those, 
            returns json response w zip, 
        now in js we have a zipfile of images
        unpack those, 
        load to body.append.

        LATER, add additional info like also API call to Zestimate, distance to nearest attractions, etc.
    */

    $('#submit').on('click',function(event){
         event.preventDefault();
         $.ajax({
            type: 'POST',
            url: "/analyzer/submit",
            headers: {
                "X-CSRFToken" : csrf,
                "Content-Type": "application/json"
            },
            data : JSON.stringify({ 
                addresses : $('#pac-input').val(),
                }),
            dataType : 'json',
            contentType : 'application/json',
            success: function (data) {
                console.log(JSON.stringify(data));
                data.responses.forEach(x=>{
                    var title = document.createElement('div');
                    title.innerHTML=x.address;
                    document.body.appendChild(title)
                    x.images.forEach(imageBase64=>{
                        var img = document.createElement('img');
                        // Set the 'src' attribute of the <img> element to the base64 data URI
                        img.src = 'data:image/jpeg;base64,' + imageBase64; // Replace 'image/jpeg' with the appropriate image MIME type

                        document.body.appendChild(img);
                 
                    })

                   }); 
           },
            error: function (e) {
                alert('no:'+e);
            },
        });
    });
});



