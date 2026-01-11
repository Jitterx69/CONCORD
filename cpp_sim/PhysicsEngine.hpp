#ifndef PHYSICS_ENGINE_HPP
#define PHYSICS_ENGINE_HPP

#include <cmath>
#include <string>
#include <vector>

/**
 * @brief Represents a point in 3D space.
 */
struct Point3D {
  double x, y, z;
};

/**
 * @brief Represents a node in the grid for pathfinding.
 */
struct SearchNode {
  int x, y;
  double g_score; // Cost from start
  double h_score; // Heuristic to goal

  // Priority queue inversion: lowest cost has highest priority
  bool operator>(const SearchNode &other) const {
    return (g_score + h_score) > (other.g_score + other.h_score);
  }
};

/**
 * @class PhysicsEngine
 * @brief Core engine for spatial calculations, collision detection, and
 * pathfinding.
 *
 * Handles simulation of entity movement and physical interactions within the
 * narrative world.
 */
class PhysicsEngine {
public:
  PhysicsEngine() = default;

  /**
   * @brief Calculates the Euclidean distance between two 3D points.
   */
  double calculateDistance(const Point3D &p1, const Point3D &p2) const;

  /**
   * @brief Estimates travel time in minutes based on transport mode.
   *
   * @param p1 Start point
   * @param p2 End point
   * @param mode Transport mode ("walking", "driving", "running", "flying")
   * @return double Estimated time in minutes
   */
  double estimateTravelTime(const Point3D &p1, const Point3D &p2,
                            const std::string &mode) const;

  /**
   * @brief Checks for collision between two spherical objects.
   */
  bool checkCollision(const Point3D &p1, double r1, const Point3D &p2,
                      double r2) const;

  /**
   * @brief Finds the shortest path on a 100x100 grid using A* algorithm.
   *
   * @return Total path cost, or -1.0 if unreachable.
   */
  double findShortestPath(int startX, int startY, int targetX, int targetY);
};

// C-compatible interface for Python/Ctypes binding
extern "C" {
double api_estimate_travel_time(double x1, double y1, double z1, double x2,
                                double y2, double z2, const char *mode);

double api_find_shortest_path(int startX, int startY, int targetX, int targetY);
}

#endif // PHYSICS_ENGINE_HPP
