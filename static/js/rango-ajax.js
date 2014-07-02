/**
 * Created by Manuel on 01.07.14.
 */
$(document).ready(function() {

        $('#likes').click(function() {
           var catid;
            catid = $(this).attr("data-catid");
            $.get('/DjangoTest/like_category/', { category_id: catid }, function(data) {
               $('#like-count').html(data);
               $('#likes').hide();
            });
        });

        $('#suggestion').keyup(function(){
            var query;
            query = $(this).val();
            $.get('/DjangoTest/suggest_category/', { suggestion: query }, function(data){
               $('#cats').html(data)
            });
        });

});