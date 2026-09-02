jQuery(function ($) {
  // Sticky header
  if ($("body").hasClass("sticky-header")) {
    var header = $("#sp-header");

    if (header.length) {
      var headerHeight = header.outerHeight();
      var stickyHeaderTop = header.offset().top;

      header.before('<div class="nav-placeholder"></div>');

      var stickyHeader = function () {
        var scrollTop = $(window).scrollTop();

        if (scrollTop > stickyHeaderTop) {
          header.addClass("header-sticky");
          $(".nav-placeholder").height(headerHeight);
        } else if (header.hasClass("header-sticky")) {
          header.removeClass("header-sticky");
          $(".nav-placeholder").height("inherit");
        }
      };

      stickyHeader();
      $(window).on("scroll", stickyHeader);
    }
  }

  // Mega menu positioning
  $(".sp-megamenu-wrapper")
    .parent()
    .parent()
    .css("position", "static")
    .parent()
    .css("position", "relative");

  // Offcanvas mobile menu
  $("#offcanvas-toggler").on("click", function (event) {
    event.preventDefault();
    $(".offcanvas-init").addClass("offcanvas-active");
  });

  $(".close-offcanvas, .offcanvas-overlay").on("click", function (event) {
    event.preventDefault();
    $(".offcanvas-init").removeClass("offcanvas-active");
  });

});
