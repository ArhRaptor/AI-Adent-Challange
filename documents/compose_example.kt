package example.inventory

data class Product(
    val id: Long,
    val name: String,
    val quantity: Int,
    val warehouse: String
)

data class InventoryUiState(
    val isLoading: Boolean = false,
    val query: String = "",
    val products: List<Product> = emptyList(),
    val error: String? = null
)

interface InventoryRepository {
    suspend fun search(query: String): List<Product>
}

class SearchInventoryUseCase(
    private val repository: InventoryRepository
) {
    suspend operator fun invoke(query: String): List<Product> {
        val normalized = query.trim()
        if (normalized.isEmpty()) return emptyList()
        return repository.search(normalized)
    }
}

/*
The ViewModel is responsible for presentation state.
A production implementation would expose StateFlow<InventoryUiState>,
launch repository work in viewModelScope, map exceptions into UI state,
and keep Android Context outside the ViewModel.
*/

class InventoryStateReducer {
    fun loading(old: InventoryUiState): InventoryUiState =
        old.copy(isLoading = true, error = null)

    fun success(
        old: InventoryUiState,
        products: List<Product>
    ): InventoryUiState =
        old.copy(isLoading = false, products = products, error = null)

    fun failure(
        old: InventoryUiState,
        message: String
    ): InventoryUiState =
        old.copy(isLoading = false, error = message)
}

/*
Structured chunking for Kotlin can be extended to recognize:
- package and import blocks
- class declarations
- interface declarations
- object declarations
- top-level functions

A regex-based parser is useful for a course demonstration, but a real parser
is more reliable for nested syntax, annotations, generics, and multiline declarations.
*/
