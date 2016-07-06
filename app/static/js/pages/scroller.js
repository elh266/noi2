$(function () {
  $('.js-scroll-btn').click(function(e) {
    var scrollPixels = 150;
    if ($(this).hasClass('js-left')) { scrollPixels *= -1; }

    $($(this).attr('data-target')).animate({
        scrollLeft: $($(this).attr('data-target')).scrollLeft() + scrollPixels
    }, 200, 'swing' );
  });
});