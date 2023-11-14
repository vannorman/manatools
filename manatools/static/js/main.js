var autoImageFn
var autoImageFn2
$(document).ready(function(){
   addEventListener("animationend", (event) => {
  });
    $('.nav.services').on('click',function(){
        $('html, body').animate({
            scrollTop: $('#services').offset().top
        }, 850); // Adjust the duration (in milliseconds) as needed});
    });
    $('#mainImage .a').css('background-image',getImage(images.length-1));
    $('#mainImage .b').css('background-image',getImage(0));

    const factor = 1000;
    autoImageFn = setInterval(function(){
        setTimeout(function(){
            $('#mainImage .b').addClass('animateBg');
        },factor*1);
        autoImageFn2 = setTimeout(function(){
            const prevImage = $('#mainImage .b').css('background-image');
            const nextImage = getNextImage();
            $('#mainImage .a').css('background-image',prevImage);
            $('#mainImage .b').css('background-image',nextImage).removeClass('animateBg');
                 
        },factor*3.5);
    },factor*5) 

    $('#leftArrow').on('click',function(){
        NavLeft();
    });
    $('#rightArrow').on('click',function(){
        NavRight();
    });
});

function NavLeft(){
    clearInterval(autoImageFn);
    clearTimeout(autoImageFn2);
    imageIndex--;
    imageIndex = imageIndex < 0 ? images.length - 1 : imageIndex;
    imageIndex %= images.length;
    $('#mainImag .b').stop();
    $('#mainImage .a').css('background-image',getImage(imageIndex));
    $('#mainImage .b').removeClass('animateBg');
}
function NavRight(){
    clearInterval(autoImageFn);
    clearTimeout(autoImageFn2);
    imageIndex++;
    imageIndex %= images.length;
    $('#mainImag .b').stop();
    $('#mainImage .a').css('background-image',getImage(imageIndex));
    $('#mainImage .b').removeClass('animateBg');

}

$(document).keydown(function(e) {
    if (e.key == "ArrowLeft") NavLeft();
    if (e.key == "ArrowRight") NavRight();
});

var imageIndex = 0;
var images = [
//'01-studio-0before.jpg',
'01-studio-after.jpg',
'01-studio-render.jpg',
//'02-shed-0before.jpg',
'02-shed-1after.jpg',
//'03-pad-0before.jpg',
'03-pad-after.jpg',
//'04-deck-0before.jpeg',
//'04-deck-after.jpeg',
'05-deck.jpeg',
'07-baths.jpg',
'08-deck.jpeg',
'09-deck.jpeg',
//'11-tile-1after.jpg',
//'11-tile-1before.jpg',
//'12-van00.jpeg',
//'12-van01.jpg',
'12-van02.jpg',
'13-van03.jpg',
'10-keys.jpg',
]

function getImage(i){
    return "url('/static/img/gallery/"+images[i]+"')";
}

function getNextImage(){
    imageIndex++;
    imageIndex%=images.length;
    return getImage(imageIndex);
}
