#include "vector_store.h"
#include <assert.h>
#include <stdio.h>

int main() {
  VectorStore *store = vs_create(10);

  // Test Vectors (2D for simplicity)
  float v1[] = {1.0, 0.0};     // X-axis
  float v2[] = {0.0, 1.0};     // Y-axis
  float v3[] = {0.707, 0.707}; // 45 degrees

  vs_add(store, v1, 2); // Idx 0
  vs_add(store, v2, 2); // Idx 1
  vs_add(store, v3, 2); // Idx 2

  // Query: (1, 0) should match v1 (0) exactly
  float q1[] = {1.0, 0.0};
  int idx1 = vs_find_nearest(store, q1, 2);
  printf("Nearest to [1,0]: %d\n", idx1);
  assert(idx1 == 0);

  // Query: (0.5, 0.5) should match v3 (2) best
  float q2[] = {0.5, 0.5};
  int idx2 = vs_find_nearest(store, q2, 2);
  printf("Nearest to [0.5,0.5]: %d\n", idx2);
  assert(idx2 == 2);

  vs_free(store);
  printf("ALL TESTS PASSED\n");
  return 0;
}
