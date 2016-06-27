function initAutocomplete(){
    $('#product_autocomplete').autocomplete({
        serviceUrl: '/autocomplete/product',
        params: {},
        onSelect: function (suggestion) {
            window.location = '/product/' + suggestion.data
        }
    })
}