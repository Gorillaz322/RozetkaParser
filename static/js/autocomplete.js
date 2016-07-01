function initAutocomplete(){
    $('#search-input').autocomplete({
        serviceUrl: '/autocomplete/product',
        params: {},
        onSelect: function (suggestion) {
            window.location = '/product/' + suggestion.data
        }
    })
}