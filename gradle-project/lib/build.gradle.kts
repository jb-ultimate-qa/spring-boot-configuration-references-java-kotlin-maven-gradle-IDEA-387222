plugins {
    `java-library`
    kotlin("jvm")
}
val springBootVersion: String by project
java { toolchain { languageVersion = JavaLanguageVersion.of(21) } }
kotlin { jvmToolchain(21) }
dependencies {
    api(platform("org.springframework.boot:spring-boot-dependencies:$springBootVersion"))
    api("org.springframework.boot:spring-boot-starter")
    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}
tasks.test { useJUnitPlatform() }
