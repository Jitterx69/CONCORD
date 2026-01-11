#include "PhysicsEngine.hpp"
#include <map>
#include <queue>

namespace {
constexpr double SPEED_WALKING_KMH = 5.0;
constexpr double SPEED_RUNNING_KMH = 10.0;
constexpr double SPEED_DRIVING_KMH = 50.0;
constexpr double SPEED_FLYING_KMH = 800.0;

constexpr int GRID_SIZE = 100;

// Obstacle definition (Mountain range simulation)
const int OBSTACLE_X_MIN = 50;
const int OBSTACLE_X_MAX = 60;
const int OBSTACLE_Y_MIN = 50;
const int OBSTACLE_Y_MAX = 60;
} // namespace

double PhysicsEngine::calculateDistance(const Point3D &p1,
                                        const Point3D &p2) const {
  return std::sqrt(std::pow(p2.x - p1.x, 2) + std::pow(p2.y - p1.y, 2) +
                   std::pow(p2.z - p1.z, 2));
}

double PhysicsEngine::estimateTravelTime(const Point3D &p1, const Point3D &p2,
                                         const std::string &mode) const {
  double dist_km = calculateDistance(p1, p2);
  double speed_kmh = SPEED_WALKING_KMH;

  if (mode == "driving")
    speed_kmh = SPEED_DRIVING_KMH;
  else if (mode == "running")
    speed_kmh = SPEED_RUNNING_KMH;
  else if (mode == "flying")
    speed_kmh = SPEED_FLYING_KMH;

  return (dist_km / speed_kmh) * 60.0; // Return minutes
}

bool PhysicsEngine::checkCollision(const Point3D &p1, double r1,
                                   const Point3D &p2, double r2) const {
  return calculateDistance(p1, p2) <= (r1 + r2);
}

double PhysicsEngine::findShortestPath(int startX, int startY, int targetX,
                                       int targetY) {
  // Bounds check
  if (startX < 0 || startX >= GRID_SIZE || startY < 0 || startY >= GRID_SIZE)
    return -1.0;

  std::priority_queue<SearchNode, std::vector<SearchNode>,
                      std::greater<SearchNode>>
      open_set;

  // Heuristic: Straight line distance ignoring Z axis
  double initial_h = calculateDistance({(double)startX, (double)startY, 0},
                                       {(double)targetX, (double)targetY, 0});
  open_set.push({startX, startY, 0.0, initial_h});

  std::map<std::pair<int, int>, double> g_scores;
  g_scores[{startX, startY}] = 0.0;

  // 4-Directional movement vectors
  const int dx[] = {0, 0, 1, -1};
  const int dy[] = {1, -1, 0, 0};

  while (!open_set.empty()) {
    SearchNode current = open_set.top();
    open_set.pop();

    if (current.x == targetX && current.y == targetY) {
      return g_scores[{current.x, current.y}];
    }

    for (int i = 0; i < 4; i++) {
      int nextX = current.x + dx[i];
      int nextY = current.y + dy[i];

      // Validate bounds
      if (nextX >= 0 && nextX < GRID_SIZE && nextY >= 0 && nextY < GRID_SIZE) {
        // Validate obstacle (simulated terrain)
        bool is_obstacle =
            (nextX >= OBSTACLE_X_MIN && nextX <= OBSTACLE_X_MAX &&
             nextY >= OBSTACLE_Y_MIN && nextY <= OBSTACLE_Y_MAX);

        if (is_obstacle)
          continue;

        double new_g_score =
            g_scores[{current.x, current.y}] + 1.0; // Cost is 1 per step

        auto next_pos = std::make_pair(nextX, nextY);
        if (g_scores.find(next_pos) == g_scores.end() ||
            new_g_score < g_scores[next_pos]) {
          g_scores[next_pos] = new_g_score;
          double h = calculateDistance({(double)nextX, (double)nextY, 0},
                                       {(double)targetX, (double)targetY, 0});
          open_set.push({nextX, nextY, new_g_score, h});
        }
      }
    }
  }

  return -1.0; // Unreachable
}

// C-API Implementation
extern "C" {
double api_estimate_travel_time(double x1, double y1, double z1, double x2,
                                double y2, double z2, const char *mode) {
  PhysicsEngine engine;
  return engine.estimateTravelTime({x1, y1, z1}, {x2, y2, z2},
                                   std::string(mode));
}

double api_find_shortest_path(int startX, int startY, int targetX,
                              int targetY) {
  PhysicsEngine engine;
  return engine.findShortestPath(startX, startY, targetX, targetY);
}
}
