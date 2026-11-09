//! Stable core for intellectism-news: URL canonicalization and JSON schema checks.

use std::collections::{HashMap, HashSet};

use serde_json::Value;

/// Canonicalize a URL for deduplication.
///
/// - lowercases scheme and host
/// - removes default ports
/// - removes fragments
/// - removes tracking parameters
/// - sorts query parameters
/// - removes a trailing slash except for the root
pub fn normalize_url(input: &str) -> String {
    let mut url = match url::Url::parse(input) {
        Ok(url) => url,
        Err(_) => return input.to_string(),
    };

    url.set_fragment(None);

    let scheme = url.scheme().to_lowercase();
    let _ = url.set_scheme(&scheme);

    if let Some(host) = url.host_str().map(str::to_lowercase) {
        let _ = url.set_host(Some(&host));
    }

    if (scheme == "http" && url.port() == Some(80))
        || (scheme == "https" && url.port() == Some(443))
    {
        let _ = url.set_port(None);
    }

    let mut pairs: Vec<(String, String)> = url
        .query_pairs()
        .map(|(key, value)| (key.to_string(), value.to_string()))
        .collect();
    pairs.retain(|(key, _)| !is_tracking(key));
    pairs.sort();

    let query = pairs
        .iter()
        .map(|(key, value)| format!("{key}={value}"))
        .collect::<Vec<_>>()
        .join("&");
    url.set_query(if query.is_empty() { None } else { Some(&query) });

    let path = url.path().to_string();
    if path.len() > 1 && path.ends_with('/') {
        url.set_path(&path[..path.len() - 1]);
    }

    url.to_string()
}

fn is_tracking(key: &str) -> bool {
    let key = key.to_lowercase();
    key.starts_with("utm_")
        || matches!(
            key.as_str(),
            "fbclid" | "gclid" | "mc_cid" | "mc_eid" | "ref" | "ref_src" | "source"
        )
}

fn is_http_url(value: &str) -> bool {
    match url::Url::parse(value) {
        Ok(url) => matches!(url.scheme(), "http" | "https"),
        Err(_) => false,
    }
}

/// Validate the daily result JSON. Returns every error, not just the first.
pub fn validate(value: &Value) -> Result<(), Vec<String>> {
    let mut errors = Vec::new();

    let Some(root) = value.as_object() else {
        return Err(vec!["root must be an object".to_string()]);
    };

    for key in [
        "date",
        "field",
        "generated_at",
        "fetched",
        "errors",
        "items",
        "candidates",
    ] {
        if !root.contains_key(key) {
            errors.push(format!("missing key: {key}"));
        }
    }

    if let Some(date) = root.get("date").and_then(Value::as_str) {
        if chrono::NaiveDate::parse_from_str(date, "%Y-%m-%d").is_err() {
            errors.push("date must be YYYY-MM-DD".to_string());
        }
    } else if root.contains_key("date") {
        errors.push("date must be a string".to_string());
    }

    if let Some(field) = root.get("field").and_then(Value::as_str) {
        if field.is_empty() {
            errors.push("field must not be empty".to_string());
        }
    } else if root.contains_key("field") {
        errors.push("field must be a string".to_string());
    }

    if let Some(generated_at) = root.get("generated_at").and_then(Value::as_str) {
        if chrono::DateTime::parse_from_rfc3339(generated_at).is_err() {
            errors.push("generated_at must be RFC 3339".to_string());
        }
    } else if root.contains_key("generated_at") {
        errors.push("generated_at must be a string".to_string());
    }

    if let Some(fetched) = root.get("fetched")
        && !fetched.is_u64()
        && !fetched.is_i64()
    {
        errors.push("fetched must be an integer".to_string());
    }

    if let Some(errors_value) = root.get("errors")
        && !errors_value.is_object()
    {
        errors.push("errors must be an object".to_string());
    }

    let mut ids: HashSet<String> = HashSet::new();
    let mut candidate_flags: HashMap<String, bool> = HashMap::new();

    if let Some(items) = root.get("items").and_then(Value::as_array) {
        if items.len() > 20 {
            errors.push("items must have at most 20".to_string());
        }

        for (index, item) in items.iter().enumerate() {
            let Some(object) = item.as_object() else {
                errors.push(format!("items[{index}] must be an object"));
                continue;
            };

            for key in [
                "id",
                "field",
                "source",
                "title",
                "url",
                "published",
                "summary",
                "score",
                "tags",
                "candidate",
            ] {
                if !object.contains_key(key) {
                    errors.push(format!("items[{index}] missing key: {key}"));
                }
            }

            let id = object.get("id").and_then(Value::as_str);
            if let Some(id) = id {
                if !ids.insert(id.to_string()) {
                    errors.push(format!("duplicate id: {id}"));
                }
            } else if object.contains_key("id") {
                errors.push(format!("items[{index}].id must be a string"));
            }

            if let (Some(item_field), Some(root_field)) = (
                object.get("field").and_then(Value::as_str),
                root.get("field").and_then(Value::as_str),
            ) && item_field != root_field
            {
                errors.push(format!("items[{index}].field mismatch"));
            }

            if let Some(url) = object.get("url").and_then(Value::as_str) {
                if !is_http_url(url) {
                    errors.push(format!("items[{index}].url is not a valid http(s) URL"));
                }
            } else if object.contains_key("url") {
                errors.push(format!("items[{index}].url must be a string"));
            }

            if let Some(published) = object.get("published").and_then(Value::as_str) {
                if chrono::DateTime::parse_from_rfc3339(published).is_err() {
                    errors.push(format!("items[{index}].published must be RFC 3339"));
                }
            } else if object.contains_key("published") {
                errors.push(format!("items[{index}].published must be a string"));
            }

            if let Some(score) = object.get("score").and_then(Value::as_f64) {
                if !score.is_finite() {
                    errors.push(format!("items[{index}].score must be finite"));
                }
            } else if object.contains_key("score") {
                errors.push(format!("items[{index}].score must be a number"));
            }

            if let Some(tags) = object.get("tags").and_then(Value::as_array) {
                if tags.iter().any(|tag| !tag.is_string()) {
                    errors.push(format!("items[{index}].tags must be strings"));
                }
            } else if object.contains_key("tags") {
                errors.push(format!("items[{index}].tags must be an array"));
            }

            if let Some(candidate) = object.get("candidate").and_then(Value::as_bool) {
                if let Some(id) = id {
                    candidate_flags.insert(id.to_string(), candidate);
                }
            } else if object.contains_key("candidate") {
                errors.push(format!("items[{index}].candidate must be a boolean"));
            }

            if let Some(primary) = object.get("primary_source")
                && !primary.is_null()
            {
                if let Some(primary) = primary.as_str() {
                    if !is_http_url(primary) {
                        errors.push(format!(
                            "items[{index}].primary_source is not a valid http(s) URL"
                        ));
                    }
                } else {
                    errors.push(format!(
                        "items[{index}].primary_source must be a string or null"
                    ));
                }
            }
        }
    } else if root.contains_key("items") {
        errors.push("items must be an array".to_string());
    }

    if let Some(candidates) = root.get("candidates").and_then(Value::as_array) {
        if candidates.len() > 10 {
            errors.push("candidates must have at most 10".to_string());
        }

        for (index, candidate) in candidates.iter().enumerate() {
            let Some(id) = candidate.as_str() else {
                errors.push(format!("candidates[{index}] must be a string"));
                continue;
            };
            if !ids.contains(id) {
                errors.push(format!("candidates[{index}] not in items: {id}"));
            }
            if candidate_flags.get(id) != Some(&true) {
                errors.push(format!("candidates[{index}] item is not candidate: {id}"));
            }
        }
    } else if root.contains_key("candidates") {
        errors.push("candidates must be an array".to_string());
    }

    if errors.is_empty() {
        Ok(())
    } else {
        Err(errors)
    }
}
