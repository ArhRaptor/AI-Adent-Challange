# Android Application Architecture

## Kotlin
Kotlin is a common language for modern Android development.
Its type system, coroutines, extension functions, and concise syntax are useful for application code.
A project should keep domain rules independent from UI details where practical.

## Jetpack Compose
Jetpack Compose uses declarative UI.
The UI describes the current state instead of manually mutating individual views.
State should flow into composables and user events should flow back toward the state holder.

## MVVM
Model-View-ViewModel separates presentation state from UI rendering.
The ViewModel exposes state and handles user intents.
Repositories or use cases can isolate data access and business logic.

## State
Immutable UI state makes screen behavior easier to reason about.
A data class can describe loading, content, selected filters, and error information.
StateFlow is commonly used to expose changing state from a ViewModel.

## Coroutines
Coroutines provide structured asynchronous programming.
A suspend function can perform asynchronous work without blocking a thread.
Scopes define lifecycle and cancellation boundaries.

## Repository Layer
A repository hides whether data comes from REST, a database, Bluetooth, or another source.
The ViewModel should not need to understand transport details.
This also makes fake repositories convenient for tests.

## Dependency Injection
Dependency injection separates object construction from object use.
Dependencies can be provided through constructors.
Dagger can generate object graphs and validate many dependency relationships at compile time.

## Navigation
Navigation Compose maps routes to composable destinations.
Applications should avoid placing unrelated business state directly inside navigation code.
Arguments should be small and stable where possible.

## Testing
ViewModel tests can use fake repositories and controlled coroutine dispatchers.
UI tests focus on visible behavior and user interactions.
Business rules should be testable without launching an Android activity.

## Error Handling
Errors should be represented in application state rather than only printed to logs.
The UI can then show retry actions or validation messages.
Technical errors may need mapping into user-facing descriptions.


# Extended Study Notes

## Review 1
This review section reinforces the concepts from android_architecture.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. ## Review 1
This review section reinforces the concepts from android_architecture.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. 

## Review 2
This review section reinforces the concepts from android_architecture.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. ## Review 2
This review section reinforces the concepts from android_architecture.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. 

## Review 3
This review section reinforces the concepts from android_architecture.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. ## Review 3
This review section reinforces the concepts from android_architecture.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. 

## Review 4
This review section reinforces the concepts from android_architecture.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. ## Review 4
This review section reinforces the concepts from android_architecture.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. 

## Review 5
This review section reinforces the concepts from android_architecture.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. ## Review 5
This review section reinforces the concepts from android_architecture.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. 

## Review 6
This review section reinforces the concepts from android_architecture.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. ## Review 6
This review section reinforces the concepts from android_architecture.md. When building an indexing corpus, repeated implementation-oriented explanations provide enough text to observe how chunk boundaries differ between strategies. The important experiment is to keep the corpus constant while changing the chunking algorithm. Metadata should remain attached to every resulting chunk. Embeddings should be generated with the same model and dimensionality so that later retrieval experiments compare like with like. Index construction should also report enough statistics to detect unexpectedly empty files, oversized sections, or an excessive number of tiny chunks. 