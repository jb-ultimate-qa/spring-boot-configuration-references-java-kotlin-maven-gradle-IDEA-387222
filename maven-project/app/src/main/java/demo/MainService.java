package demo;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class MainService {
  @Value("${my.property}")                   // TC-01
  String myProperty;

  @Value("${main.only.property}")            // TC-02
  String mainOnly;

  @Value("${yaml.property}")                 // TC-03
  String yamlProperty;

  @Value("${test.only.property}")            // NC-01, XP-01 (fold)
  String testOnly;

  @Value("${yaml.test-only:none}")           // NC-02
  String yamlTestOnly;

  @Value("${imported.test.property:none}")   // NC-03
  String importedTestOnly;

  @Value("${extra.key:none}")                // XP-01
  String extraKey;

  @Value("${integration.only.property:none}") // XP-03
  String integrationOnly;
}
