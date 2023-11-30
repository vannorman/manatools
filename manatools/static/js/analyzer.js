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
                // Create a new instance of JSZip
                var zip = new JSZip();
                var zip_data = data['zip_data']
                // Load the ZIP data
                zip.loadAsync(zip_data).then(function (zip) {
                    // Iterate through the files in the ZIP archive
                    zip.forEach(function (relativePath, file) {
                        // Read the content of each file in the ZIP archive
                        file.async('uint8array').then(function (content) {
                            // Do something with the file content, e.g., display images
                            var blob = new Blob([content], { type: 'application/octet-stream' });
                            var url = URL.createObjectURL(blob);

                            // Create an element to display the file (e.g., an image)
                            var img = document.createElement('img');
                            img.src = url;
                            document.body.appendChild(img);
                        });
                    });
                }).catch(function (error) {
                    console.error('Error decoding ZIP archive:', error);
                });

                alert('suc:'+JSON.stringify(e));
            },
            error: function (e) {
                alert('no:'+e);
            },
        });
    });
});

// Create a new instance of JSZip
var zip = new JSZip();


