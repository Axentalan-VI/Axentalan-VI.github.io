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
function linkOrNothing(url, label) {
  if (!url) return "";
  return '<a href="' + escapeHtml(url) + '" rel="noopener">' +
         escapeHtml(label) + "</a>";
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
    linkOrNothing(p.repo, "Code"),
    linkOrNothing(p.competition, "Competition"),
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
      return '<a href="' + escapeHtml(item.url) + '" rel="noopener">' +
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

function showFallback() {
  var message = '<p class="error">Project details could not be loaded. ' +
    'All of this work is on <a href="https://github.com/Axentalan-VI" ' +
    'rel="noopener">github.com/Axentalan-VI</a>.</p>';
  ["featured", "compact"].forEach(function (id) {
    var node = document.getElementById(id);
    if (node && !node.innerHTML.trim()) node.innerHTML = message;
  });
}

async function init() {
  try {
    const [profileResponse, projectsResponse] = await Promise.all([
      fetch("data/profile.json"),
      fetch("data/projects.json")
    ]);
    if (!profileResponse.ok || !projectsResponse.ok) {
      throw new Error("failed to load site data");
    }
    renderProfile(await profileResponse.json());
    renderProjects(await projectsResponse.json());
    wireFilter();
  } catch (error) {
    console.error(error);
    showFallback();
  }
}

init();
