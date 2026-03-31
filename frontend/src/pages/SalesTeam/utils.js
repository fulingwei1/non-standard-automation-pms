/**
 * SalesTeam page utility functions
 */

/**
 * Get color class based on achievement rate
 */
export function getRateColor(rate) {
  if (rate >= 70) return "text-green-500";
  if (rate >= 60) return "text-blue-500";
  if (rate >= 50) return "text-orange-500";
  return "text-red-500";
}

/**
 * Generate a team code based on current timestamp
 */
export function generateTeamCode() {
  return `TEAM${Date.now().toString().slice(-8)}`;
}

/**
 * Filter team members by search keyword
 */
export function filterMembersBySearch(members, searchTerm) {
  if (!searchTerm) return members;
  const keyword = searchTerm.toLowerCase();
  return (members || []).filter((member) => {
    const name = member.name?.toLowerCase?.() || "";
    const role = member.role?.toLowerCase?.() || "";
    const regionText = member.region?.toLowerCase?.() || "";
    return name.includes(keyword) || role.includes(keyword) || regionText.includes(keyword);
  });
}
