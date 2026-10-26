#nullable enable
using System;
using System.Collections.Generic;
using System.Linq;
using System.Xml.Linq;

namespace NavigatorKit.Core;

public static class MappingProfile
{
    public static List<StampTemplate> Load(string xmlPath)
    {
        var doc = XDocument.Load(xmlPath);
        var list = new List<StampTemplate>();
        foreach (var node in doc.Descendants("template"))
        {
            var template = new StampTemplate
            {
                Id = (string?)node.Attribute("id") ?? string.Empty,
                BlockName = (string?)node.Attribute("blockName") ?? string.Empty,
                Description = (string?)node.Attribute("description") ?? string.Empty,
                Status = (string?)node.Attribute("status") ?? string.Empty
            };
            foreach (var attr in node.Elements("attribute"))
            {
                var tag = (string?)attr.Attribute("tag") ?? string.Empty;
                var field = (string?)attr.Attribute("field") ?? string.Empty;
                if (string.IsNullOrWhiteSpace(tag) || string.IsNullOrWhiteSpace(field)) continue;
                template.TagToField[tag] = field;
                if (string.Equals((string?)attr.Attribute("required"), "true", StringComparison.OrdinalIgnoreCase))
                    template.RequiredFields.Add(field);
            }
            list.Add(template);
        }
        if (list.Count == 0) throw new InvalidOperationException("No stamp templates in XML mapping");
        return list;
    }

    public static StampTemplate? Select(IReadOnlyDictionary<string, string> attrs, IReadOnlyList<StampTemplate> templates)
    {
        foreach (var p in templates)
        {
            var tag = p.TagToField.FirstOrDefault(x => x.Value == "profile_id").Key;
            if (!string.IsNullOrEmpty(tag) &&
                attrs.TryGetValue(tag, out var id) &&
                string.Equals(id, p.Id, StringComparison.OrdinalIgnoreCase))
                return p;
        }
        StampTemplate? best = null;
        var bestScore = 0;
        foreach (var p in templates)
        {
            var score = p.TagToField.Keys.Count(attrs.ContainsKey);
            if (score > bestScore) { bestScore = score; best = p; }
        }
        return bestScore >= 3 ? best : null;
    }
}
