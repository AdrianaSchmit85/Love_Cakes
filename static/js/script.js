
   
/*
    jQuery for MaterializeCSS initialization
*/

$(document).ready(function () {
    $(".sidenav").sidenav({edge: "right"});
    M.updateTextFields();
});



function deleteRecipe(id){
    var confirm = window.confirm("Delete?")
    if(confirm){
        window.location.href = `/delete-recipe/${id}`;
    }
}
