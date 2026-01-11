#include "PhysicsEngine.hpp"
#include <cassert>
#include <iostream>

int main() {
  PhysicsEngine engine;

  // Test Distance (3-4-5 triangle)
  Point3D p1 = {0, 0, 0};
  Point3D p2 = {3, 4, 0};
  double dist = engine.calculateDistance(p1, p2);
  std::cout << "Distance (3,4,0): " << dist << std::endl;
  assert(std::abs(dist - 5.0) < 0.001);

  // Test Travel Time (Driving 50km/h for 5km)
  double time = engine.estimateTravelTime(p1, p2, "driving");
  std::cout << "Time (Driving 5km): " << time << " mins" << std::endl;
  assert(std::abs(time - 6.0) < 0.001); // 5km / 50kmh = 0.1h = 6 mins

  std::cout << "ALL TESTS PASSED" << std::endl;
  return 0;
}
