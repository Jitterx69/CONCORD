#include "vector_store.h"
#include <float.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

VectorStore *vs_create(size_t initial_capacity) {
  VectorStore *store = (VectorStore *)malloc(sizeof(VectorStore));
  store->vectors = (Vector *)malloc(sizeof(Vector) * initial_capacity);
  store->count = 0;
  store->capacity = initial_capacity;
  return store;
}

void vs_add(VectorStore *store, float *data, size_t dim) {
  if (store->count >= store->capacity) {
    // Simple expansion
    store->capacity *= 2;
    store->vectors =
        (Vector *)realloc(store->vectors, sizeof(Vector) * store->capacity);
  }

  Vector *v = &store->vectors[store->count];
  v->dimension = dim;
  v->data = (float *)malloc(sizeof(float) * dim);
  memcpy(v->data, data, sizeof(float) * dim);

  store->count++;
}

float vs_dot_product(float *v1, float *v2, size_t dim) {
  float sum = 0.0f;
  for (size_t i = 0; i < dim; i++) {
    sum += v1[i] * v2[i];
  }
  return sum;
}

static float magnitude(float *v, size_t dim) {
  float sum = 0.0f;
  for (size_t i = 0; i < dim; i++) {
    sum += v[i] * v[i];
  }
  return sqrtf(sum);
}

int vs_find_nearest(VectorStore *store, float *query, size_t dim) {
  int best_idx = -1;
  float best_sim = -FLT_MAX;

  float query_mag = magnitude(query, dim);
  if (query_mag == 0)
    return -1;

  for (size_t i = 0; i < store->count; i++) {
    Vector *v = &store->vectors[i];
    if (v->dimension != dim)
      continue;

    float dot = vs_dot_product(v->data, query, dim);
    float mag = magnitude(v->data, dim);

    if (mag == 0)
      continue;

    float sim = dot / (mag * query_mag);
    if (sim > best_sim) {
      best_sim = sim;
      best_idx = (int)i;
    }
  }

  return best_idx;
}

void vs_free(VectorStore *store) {
  for (size_t i = 0; i < store->count; i++) {
    free(store->vectors[i].data);
  }
  free(store->vectors);
  free(store);
}
