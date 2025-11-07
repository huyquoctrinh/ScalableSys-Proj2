// Save as tests/questions.cypher
// Assumed schema (adjust names if needed):
// (:Laureate {name})-[:WON]->(:Prize {category, year})
// (:Laureate)-[:AFFILIATED_WITH]->(:Institution {name})
// (:Laureate)-[:BORN_IN]->(:City {name})
// (:Institution)-[:LOCATED_IN]->(:City)
// (:City)-[:IN_COUNTRY]->(:Country {name})
// (:Country)-[:IN_CONTINENT]->(:Continent {name})

/* 1) Physics laureates in 1921 */
MATCH (l:Laureate)-[:WON]->(p:Prize {category:"Physics", year:1921})
RETURN DISTINCT l.name
ORDER BY l.name;

/* 2) Laureates with more than one Nobel Prize */
MATCH (l:Laureate)-[:WON]->(p:Prize)
WITH l, count(p) AS prizes
WHERE prizes > 1
RETURN l.name, prizes
ORDER BY prizes DESC, l.name;

/* 3) Laureates affiliated with University of Cambridge */
MATCH (l:Laureate)-[:AFFILIATED_WITH]->(i:Institution)
WHERE i.name CONTAINS "University of Cambridge"
RETURN DISTINCT l.name
ORDER BY l.name;

/* 4) How many laureates were born in Germany */
MATCH (l:Laureate)-[:BORN_IN]->(:City)-[:IN_COUNTRY]->(c:Country {name:"Germany"})
RETURN count(DISTINCT l) AS laureates_from_germany;

/* 5) Chemistry laureates after 2000 */
MATCH (l:Laureate)-[:WON]->(p:Prize {category:"Chemistry"})
WHERE p.year > 2000
RETURN l.name, p.year
ORDER BY p.year, l.name;

/* 6) Institutions in the USA with laureates in Physiology or Medicine */
MATCH (i:Institution)-[:LOCATED_IN]->(:City)-[:IN_COUNTRY]->(c:Country {name:"United States"})
MATCH (l:Laureate)-[:AFFILIATED_WITH]->(i)
MATCH (l)-[:WON]->(p:Prize {category:"Physiology or Medicine"})
RETURN DISTINCT i.name
ORDER BY i.name;

/* 7) Laureates born in cities within France */
MATCH (l:Laureate)-[:BORN_IN]->(city:City)-[:IN_COUNTRY]->(:Country {name:"France"})
RETURN DISTINCT l.name, city.name
ORDER BY l.name;

/* 8) Peace laureates affiliated with orgs in Switzerland */
MATCH (l:Laureate)-[:WON]->(p:Prize {category:"Peace"})
MATCH (l)-[:AFFILIATED_WITH]->(i:Institution)-[:LOCATED_IN]->(:City)-[:IN_COUNTRY]->(:Country {name:"Switzerland"})
RETURN DISTINCT l.name, i.name
ORDER BY l.name;

/* 9) Top 3 countries by number of laureates (by birthplace) */
MATCH (l:Laureate)-[:BORN_IN]->(:City)-[:IN_COUNTRY]->(c:Country)
WITH c.name AS country, count(DISTINCT l) AS n
RETURN country, n
ORDER BY n DESC
LIMIT 3;

/* 10) Economic Sciences laureates in the 2010s */
MATCH (l:Laureate)-[:WON]->(p:Prize {category:"Economic Sciences"})
WHERE p.year >= 2010 AND p.year < 2020
RETURN l.name, p.year
ORDER BY p.year, l.name;

/* 11) Laureates born on the continent of Asia */
MATCH (l:Laureate)-[:BORN_IN]->(:City)-[:IN_COUNTRY]->(:Country)-[:IN_CONTINENT]->(ct:Continent {name:"Asia"})
RETURN DISTINCT l.name
ORDER BY l.name;

/* 12) Laureates affiliated with MIT who won Physics 1950–2000 */
MATCH (l:Laureate)-[:AFFILIATED_WITH]->(i:Institution)
WHERE i.name CONTAINS "MIT"
MATCH (l)-[:WON]->(p:Prize {category:"Physics"})
WHERE p.year >= 1950 AND p.year <= 2000
RETURN DISTINCT l.name, p.year
ORDER BY p.year, l.name;

/* 13) Laureates with affiliations in Cambridge AND Oxford */
MATCH (l:Laureate)-[:AFFILIATED_WITH]->(i1:Institution)
WHERE i1.name CONTAINS "Cambridge"
WITH DISTINCT l
MATCH (l)-[:AFFILIATED_WITH]->(i2:Institution)
WHERE i2.name CONTAINS "Oxford"
RETURN DISTINCT l.name
ORDER BY l.name;

/* 14) Laureates who won both Physics and Chemistry */
MATCH (l:Laureate)-[:WON]->(:Prize {category:"Physics"})
MATCH (l)-[:WON]->(:Prize {category:"Chemistry"})
RETURN DISTINCT l.name
ORDER BY l.name;

/* 15) Institutions in Germany with more than 3 Nobel laureates */
MATCH (i:Institution)-[:LOCATED_IN]->(:City)-[:IN_COUNTRY]->(:Country {name:"Germany"})
MATCH (l:Laureate)-[:AFFILIATED_WITH]->(i)
WITH i, count(DISTINCT l) AS n
WHERE n > 3
RETURN i.name AS institution, n
ORDER BY n DESC, institution;
