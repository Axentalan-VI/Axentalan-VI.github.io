/* Renders the portfolio from data/profile.json and data/projects.json.
   No dependencies. Every value from JSON is escaped before it reaches
   innerHTML, and a missing URL renders no anchor at all. */

function escapeHtml(value) {
  return String(value === null || value === undefined ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/* Returns an anchor, or an empty string when there is no URL.
   A null repo or competition must leave no trace in the markup. */
function linkOrNothing(url, label, context) {
  if (!url) return "";
  // target=_blank keeps the portfolio open behind the repo the reader opened;
  // rel=noopener is what makes that safe, and is meaningless without it.
  // The label is repeated for every card, so give screen readers the context.
  var aria = context ? ' aria-label="' + escapeHtml(label + " - " + context) +
             '"' : "";
  return '<a href="' + escapeHtml(url) + '" target="_blank" rel="noopener"' +
         aria + ">" + escapeHtml(label) + "</a>";
}

function tagList(tags) {
  return '<div class="tags">' +
    tags.map(function (t) {
      return '<span class="tag">' + escapeHtml(t) + "</span>";
    }).join("") + "</div>";
}

function bulletList(items) {
  if (!items || !items.length) return "";
  return "<ul>" + items.map(function (b) {
    return "<li>" + escapeHtml(b) + "</li>";
  }).join("") + "</ul>";
}

var STATUS_LABEL = {
  "in-progress": "In progress",
  "submitted": "Submitted",
  "completed": "Completed"
};

function projectCard(p) {
  var parts = [];
  parts.push("<h3>" + escapeHtml(p.title) + "</h3>");
  parts.push('<p class="problem">' + escapeHtml(p.problem) + "</p>");

  if (p.outcome) {
    parts.push(
      '<p class="outcome"><span class="outcome-value">' +
      escapeHtml(p.outcome.value) + "</span> " +
      escapeHtml(p.outcome.metric) +
      ' <span class="outcome-context">' +
      escapeHtml(p.outcome.context) + "</span></p>"
    );
  }

  if (p.featured) {
    parts.push(bulletList(p.approach));
    if (p.constraint) {
      parts.push('<p class="constraint"><strong>Constraint:</strong> ' +
                 escapeHtml(p.constraint) + "</p>");
    }
  }

  parts.push(tagList(p.tags));

  var foot = [
    linkOrNothing(p.repo, "Code", p.title),
    linkOrNothing(p.competition, "Competition", p.title),
    '<span class="badge">' + escapeHtml(STATUS_LABEL[p.status] || p.status) +
      "</span>"
  ].filter(Boolean).join("");

  parts.push('<div class="card-foot">' + foot + "</div>");

  return '<article class="card" id="' + escapeHtml(p.id) +
         '" data-track="' + escapeHtml(p.track) + '">' +
         parts.join("") + "</article>";
}

function renderProfile(profile) {
  document.getElementById("link-row").innerHTML = profile.links
    .map(function (item) {
      var external = item.url.indexOf("http") === 0;
      return '<a href="' + escapeHtml(item.url) + '"' +
             (external ? ' target="_blank" rel="noopener"' : "") + ">" +
             escapeHtml(item.label) + "</a>";
    }).join("");

  document.getElementById("profile-text").textContent = profile.profile;

  document.getElementById("experience").innerHTML = profile.experience
    .map(function (entry) {
      return '<div class="job"><div class="job-head">' +
        '<span class="job-role">' + escapeHtml(entry.role) + "</span>" +
        '<span class="job-org">' + escapeHtml(entry.organization) + "</span>" +
        '<span class="job-dates">' + escapeHtml(entry.dates) + "</span>" +
        "</div>" + bulletList(entry.bullets) + "</div>";
    }).join("");

  document.getElementById("skills").innerHTML = profile.skills
    .map(function (group) {
      return '<div class="skill-group"><h3>' + escapeHtml(group.group) +
             "</h3>" + tagList(group.items) + "</div>";
    }).join("");

  var edu = profile.education;
  document.getElementById("education").innerHTML =
    '<div class="job"><div class="job-head">' +
    '<span class="job-role">' + escapeHtml(edu.degree) + "</span>" +
    '<span class="job-org">' + escapeHtml(edu.institution) + "</span>" +
    '<span class="job-dates">' + escapeHtml(edu.dates) + "</span></div>" +
    "<p>" + escapeHtml(edu.detail) + "</p></div>";

  document.getElementById("certifications").innerHTML = profile.certifications
    .map(function (item) { return "<li>" + escapeHtml(item) + "</li>"; })
    .join("");
}

function renderProjects(projects) {
  document.getElementById("featured").innerHTML = projects
    .filter(function (p) { return p.featured; })
    .map(projectCard).join("");

  document.getElementById("compact").innerHTML = projects
    .filter(function (p) { return !p.featured; })
    .map(projectCard).join("");
}

function wireFilter() {
  var buttons = document.querySelectorAll(".filter button[data-track]");
  Array.prototype.forEach.call(buttons, function (button) {
    button.addEventListener("click", function () {
      var track = button.getAttribute("data-track");
      Array.prototype.forEach.call(buttons, function (other) {
        other.classList.toggle("is-active", other === button);
      });
      var cards = document.querySelectorAll(".card[data-track]");
      Array.prototype.forEach.call(cards, function (card) {
        card.hidden = track !== "all" &&
                      card.getAttribute("data-track") !== track;
      });
    });
  });
}

/* Fill any mount still empty with a pointer to the GitHub profile.

   This covers every mount, not just the project grids: a failure inside
   renderProfile would otherwise leave the experience section - the strongest
   thing on the page - as a bare heading with no explanation, while the
   projects showed a "could not be loaded" message that was not even true. */
function showFallback() {
  var message = '<p class="error">This section could not be loaded. ' +
    'All of this work is on <a href="https://github.com/Axentalan-VI" ' +
    'rel="noopener">github.com/Axentalan-VI</a>.</p>';
  ["link-row", "profile-text", "experience", "featured", "compact",
   "skills", "education", "certifications"].forEach(function (id) {
    var node = document.getElementById(id);
    if (node && !node.innerHTML.trim() && !node.textContent.trim()) {
      node.innerHTML = message;
    }
  });
}

async function init() {
  var profile = null;
  var projects = null;

  try {
    const [profileResponse, projectsResponse] = await Promise.all([
      fetch("data/profile.json"),
      fetch("data/projects.json")
    ]);
    if (profileResponse.ok) profile = await profileResponse.json();
    if (projectsResponse.ok) projects = await projectsResponse.json();
  } catch (error) {
    console.error(error);
  }

  /* Render each half independently, so one bad file cannot blank the other
     and so wireFilter still runs when the projects themselves are fine. */
  if (profile) {
    try {
      renderProfile(profile);
    } catch (error) {
      console.error(error);
    }
  }
  if (projects) {
    try {
      renderProjects(projects);
      wireFilter();
    } catch (error) {
      console.error(error);
    }
  }

  showFallback();
}

init();
