$(document).ready( function() {

    $('#likes').click(function(){
    var catid;
    catid = $(this).attr("data-catid");
     $.get('/rango/like_category/', {category_id: catid}, function(data){
               $('#like_count').html(data);
               $('#likes').hide();
           });
	});

	$('#suggestion').keyup(function(){
        var query;
        query = $(this).val();
        $.get('/rango/suggest_category/', {suggestion: query}, function(data){
         $('#cats').html(data);
        });
	});

	$(".rango-add").click(function() {
		var catid
		var pageurl
		var pagetitle

		catid = $(this).attr("data-catid");
		pageurl = $(this).attr("data-url");
		pagetitle = $(this).attr("data-title");
		
		$.get('/rango/auto_add_page/',
			  { "category_id" : catid, "url" : pageurl, "title" : pagetitle},
			  function(data) {
				  $(".rango-add").hide();
				  $("#pages").html(data);
			  });
	});
});
