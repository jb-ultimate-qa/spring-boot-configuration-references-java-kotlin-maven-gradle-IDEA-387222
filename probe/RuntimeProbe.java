import java.net.URL;
import java.util.Collections;
import java.util.List;

import org.springframework.boot.Banner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.WebApplicationType;
import org.springframework.boot.origin.Origin;
import org.springframework.boot.origin.OriginLookup;
import org.springframework.boot.origin.TextResourceOrigin;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.env.ConfigurableEnvironment;
import org.springframework.core.env.PropertySource;

/**
 * Prints what Spring Boot itself loads on the classpath it runs on: every copy of a config
 * file name, the config files that Boot loaded, and the value and origin of each key.
 * No component scan, so no bean of the project fails first.
 *
 * Usage: java -cp probe/classes;PROJECT_CLASSPATH RuntimeProbe PROFILES|- KEY...
 */
public class RuntimeProbe {
  private static final String[] FILES = {
      "application.properties", "application.yml", "application-test.properties",
      "application-dev.properties", "extra-config.properties", "extra.properties"};

  @Configuration(proxyBeanMethods = false)
  static class Empty {
  }

  public static void main(String[] args) throws Exception {
    ClassLoader loader = RuntimeProbe.class.getClassLoader();
    System.out.println("classpath copies, in classpath order:");
    for (String name : FILES) {
      List<URL> urls = Collections.list(loader.getResources(name));
      for (int i = 0; i < urls.size(); i++) {
        System.out.println("  " + name + " #" + (i + 1) + ": " + urls.get(i));
      }
    }

    SpringApplication application = new SpringApplication(Empty.class);
    application.setWebApplicationType(WebApplicationType.NONE);
    application.setBannerMode(Banner.Mode.OFF);
    application.setLogStartupInfo(false);
    if (!args[0].equals("-")) {
      application.setAdditionalProfiles(args[0].split(","));
    }
    try (ConfigurableApplicationContext context = application.run()) {
      ConfigurableEnvironment environment = context.getEnvironment();
      System.out.println("config files loaded by Spring Boot:");
      for (PropertySource<?> source : environment.getPropertySources()) {
        if (source.getName().startsWith("Config resource")) {
          System.out.println("  " + source.getName() + " -> " + location(source));
        }
      }
      System.out.println("keys:");
      for (int i = 1; i < args.length; i++) {
        System.out.println("  " + args[i] + " = " + describe(environment, args[i]));
      }
    }
  }

  private static String describe(ConfigurableEnvironment environment, String key) {
    String value;
    try {
      value = environment.getProperty(key);
    }
    catch (IllegalArgumentException ex) {
      return "UNRESOLVABLE: " + ex.getMessage();
    }
    if (value == null) {
      return "ABSENT";
    }
    for (PropertySource<?> source : environment.getPropertySources()) {
      // Skip the source that Boot attaches over all others; the next match is the real file.
      if (!source.getName().equals("configurationProperties") && source.containsProperty(key)) {
        return value + "   (" + location(source) + ")";
      }
    }
    return value;
  }

  // The URL of the file behind a config property source, taken from the origin of its first key.
  private static String location(PropertySource<?> source) {
    if (source.getSource() instanceof java.util.Map<?, ?> map && !map.isEmpty()) {
      Origin origin = OriginLookup.getOrigin(source, String.valueOf(map.keySet().iterator().next()));
      if (origin instanceof TextResourceOrigin textOrigin && textOrigin.getResource() != null) {
        try {
          return textOrigin.getResource().getURL().toString();
        }
        catch (Exception ex) {
          return textOrigin.getResource().getDescription();
        }
      }
    }
    return source.getName();
  }
}
