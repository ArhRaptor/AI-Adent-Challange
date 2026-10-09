// Учебный пример представления состояния в Compose
// ViewModel управляет UI state, а composable отображает его.

data class ProductUiState(
    val searchQuery: String = "",
    val products: List<String> = emptyList(),
    val isLoading: Boolean = false
)

// В реальном приложении ViewModel обновляет StateFlow<ProductUiState>.
// Composable подписывается на состояние и отображает список товаров.
